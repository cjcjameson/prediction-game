use std::collections::{HashMap, HashSet};
use std::fs;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Instant;
use rayon::prelude::*;
use serde::Deserialize;
use indicatif::{ProgressBar, ProgressStyle};

// ============================================================================
// Data structures for JSON loading
// ============================================================================

#[derive(Debug, Deserialize)]
pub struct GameData {
    pub year: u32,
    pub questions: HashMap<String, String>,
    pub outcomes: HashMap<String, String>,
    pub predictions: HashMap<String, Vec<u32>>,
}

/// Aggregated statistics - computed on-the-fly, no need to store all 67M results
#[derive(Clone)]
pub struct Stats {
    /// How many times each contestant wins (after tie-breaking)
    pub winner_tally: HashMap<String, u64>,
    /// Total number of tie scenarios (before tie-breaking)
    pub tie_count: u64,
    /// How many scenarios each contestant could win (including ties they're part of)
    pub win_paths: HashMap<String, u64>,
    /// For each contestant, for each question index: (yes_wins, no_wins)
    pub person_question_buckets: HashMap<String, Vec<(u64, u64)>>,
    /// For each yes-count (0..=num_maybes): count per contestant
    pub yes_buckets: Vec<HashMap<String, u64>>,
}

impl Stats {
    fn new(contestants: &[String], num_questions: usize, num_maybes: usize) -> Self {
        let mut winner_tally = HashMap::new();
        let mut win_paths = HashMap::new();
        let mut person_question_buckets = HashMap::new();
        
        for name in contestants {
            winner_tally.insert(name.clone(), 0);
            win_paths.insert(name.clone(), 0);
            person_question_buckets.insert(name.clone(), vec![(0, 0); num_questions]);
        }
        
        let yes_buckets = (0..=num_maybes).map(|_| HashMap::new()).collect();
        
        Stats {
            winner_tally,
            tie_count: 0,
            win_paths,
            person_question_buckets,
            yes_buckets,
        }
    }
    
    fn merge(mut self, other: Stats) -> Stats {
        // Merge winner_tally
        for (name, count) in other.winner_tally {
            *self.winner_tally.entry(name).or_insert(0) += count;
        }
        
        // Merge tie_count
        self.tie_count += other.tie_count;
        
        // Merge win_paths
        for (name, count) in other.win_paths {
            *self.win_paths.entry(name).or_insert(0) += count;
        }
        
        // Merge person_question_buckets
        for (name, buckets) in other.person_question_buckets {
            if let Some(self_buckets) = self.person_question_buckets.get_mut(&name) {
                for (i, (y, n)) in buckets.into_iter().enumerate() {
                    self_buckets[i].0 += y;
                    self_buckets[i].1 += n;
                }
            } else {
                self.person_question_buckets.insert(name, buckets);
            }
        }
        
        // Merge yes_buckets
        for (i, bucket) in other.yes_buckets.into_iter().enumerate() {
            for (name, count) in bucket {
                *self.yes_buckets[i].entry(name).or_insert(0) += count;
            }
        }
        
        self
    }
}

// ============================================================================
// Data loading and validation
// ============================================================================

impl GameData {
    pub fn load(path: &str) -> Result<Self, String> {
        let contents = fs::read_to_string(path)
            .map_err(|e| format!("Failed to read {}: {}", path, e))?;
        let data: GameData = serde_json::from_str(&contents)
            .map_err(|e| format!("Failed to parse JSON: {}", e))?;
        Ok(data)
    }

    pub fn validate(&self) -> Result<(), Vec<String>> {
        let mut errors = Vec::new();
        let num_questions = self.questions.len();

        for key in self.outcomes.keys() {
            if !self.questions.contains_key(key) {
                errors.push(format!("Outcome '{}' has no matching question", key));
            }
        }

        for (name, rankings) in &self.predictions {
            if rankings.len() != num_questions {
                errors.push(format!(
                    "{}: has {} rankings, expected {}",
                    name, rankings.len(), num_questions
                ));
                continue;
            }

            let expected: HashSet<u32> = (1..=num_questions as u32).collect();
            let actual: HashSet<u32> = rankings.iter().copied().collect();
            
            if actual != expected {
                let missing: Vec<u32> = expected.difference(&actual).copied().collect();
                let extra: Vec<u32> = actual.difference(&expected).copied().collect();
                let mut duplicates: Vec<u32> = Vec::new();
                
                let mut seen = HashSet::new();
                for &r in rankings {
                    if !seen.insert(r) {
                        duplicates.push(r);
                    }
                }
                
                errors.push(format!(
                    "{}: invalid rankings - missing {:?}, duplicates {:?}, invalid {:?}",
                    name, missing, duplicates, extra
                ));
            }
        }

        if errors.is_empty() { Ok(()) } else { Err(errors) }
    }

    pub fn question_ids(&self) -> Vec<String> {
        let mut ids: Vec<String> = self.questions.keys().cloned().collect();
        ids.sort();
        ids
    }

    pub fn outcomes_vec(&self) -> Vec<char> {
        self.question_ids()
            .iter()
            .map(|id| {
                self.outcomes
                    .get(id)
                    .map(|s| s.chars().next().unwrap_or('m'))
                    .unwrap_or('m')
            })
            .collect()
    }

    pub fn predictions_vec(&self) -> Vec<(String, Vec<u32>)> {
        self.predictions
            .iter()
            .map(|(name, rankings)| (name.clone(), rankings.clone()))
            .collect()
    }
}

// ============================================================================
// Core algorithm - OPTIMIZED: aggregates stats on-the-fly
// ============================================================================

pub fn compute_stats(
    predictions: &[(String, Vec<u32>)],
    outcomes: &[char],
) -> Stats {
    let unresolved_indices: Vec<usize> = outcomes.iter()
        .enumerate()
        .filter(|(_, &o)| o == 'm')
        .map(|(i, _)| i)
        .collect();
    
    let num_unresolved = unresolved_indices.len();
    let num_questions = outcomes.len();
    let total_combinations = 1u64 << num_unresolved;
    let yesses_already: usize = outcomes.iter().filter(|&&o| o == 'y').count();
    
    let contestants: Vec<String> = predictions.iter().map(|(n, _)| n.clone()).collect();
    
    // Progress bar
    let progress = ProgressBar::new(total_combinations);
    progress.set_style(ProgressStyle::default_bar()
        .template("{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} ({percent}%) ETA: {eta}")
        .unwrap()
        .progress_chars("#>-"));
    
    let counter = AtomicU64::new(0);
    let update_interval = (total_combinations / 1000).max(1);
    
    // Parallel fold + reduce
    let stats = (0..total_combinations)
        .into_par_iter()
        .fold(
            || Stats::new(&contestants, num_questions, num_unresolved),
            |mut stats, i| {
                // Update progress periodically
                let count = counter.fetch_add(1, Ordering::Relaxed);
                if count % update_interval == 0 {
                    progress.set_position(count);
                }
                
                // Build outcome array
                let mut current_outcome: Vec<char> = outcomes.to_vec();
                for (bit_pos, &idx) in unresolved_indices.iter().enumerate() {
                    current_outcome[idx] = if (i >> bit_pos) & 1 == 1 { 'y' } else { 'n' };
                }
                
                // Calculate points for each contestant
                let scores: Vec<(usize, u32)> = predictions.iter()
                    .enumerate()
                    .map(|(idx, (_, rankings))| {
                        let pts = calculate_points(rankings, &current_outcome);
                        (idx, pts)
                    })
                    .collect();
                
                let max_score = scores.iter().map(|(_, s)| *s).max().unwrap();
                let winner_indices: Vec<usize> = scores.iter()
                    .filter(|(_, s)| *s == max_score)
                    .map(|(idx, _)| *idx)
                    .collect();
                
                let was_tie = winner_indices.len() > 1;
                let winner_idx = if !was_tie {
                    winner_indices[0]
                } else {
                    tie_breaker_idx(predictions, &current_outcome, &winner_indices)
                };
                
                // Update stats
                let winner_name = &contestants[winner_idx];
                *stats.winner_tally.get_mut(winner_name).unwrap() += 1;
                
                if was_tie {
                    stats.tie_count += 1;
                }
                
                // Win paths for all tied contestants
                for &idx in &winner_indices {
                    let name = &contestants[idx];
                    *stats.win_paths.get_mut(name).unwrap() += 1;
                    
                    // Question buckets
                    if let Some(buckets) = stats.person_question_buckets.get_mut(name) {
                        for (q_idx, &outcome) in current_outcome.iter().enumerate() {
                            if outcome == 'y' {
                                buckets[q_idx].0 += 1;
                            } else {
                                buckets[q_idx].1 += 1;
                            }
                        }
                    }
                }
                
                // Yes-count buckets
                let yes_count = current_outcome.iter().filter(|&&c| c == 'y').count();
                let more_yesses = yes_count - yesses_already;
                for &idx in &winner_indices {
                    let name = &contestants[idx];
                    *stats.yes_buckets[more_yesses].entry(name.clone()).or_insert(0) += 1;
                }
                
                stats
            }
        )
        .reduce(
            || Stats::new(&contestants, num_questions, num_unresolved),
            |a, b| a.merge(b)
        );
    
    progress.finish_and_clear();
    stats
}

pub fn calculate_points(rankings: &[u32], outcomes: &[char]) -> u32 {
    rankings.iter()
        .zip(outcomes.iter())
        .filter(|(_, &o)| o == 'y')
        .map(|(r, _)| *r)
        .sum()
}

/// Tie breaker that works with indices instead of names (faster)
fn tie_breaker_idx(
    predictions: &[(String, Vec<u32>)],
    outcomes: &[char],
    tied_indices: &[usize],
) -> usize {
    if tied_indices.len() == 1 {
        return tied_indices[0];
    }
    
    // Get each contestant's correct predictions sorted descending
    let mut contestant_rankings: Vec<(usize, Vec<u32>)> = tied_indices.iter()
        .map(|&idx| {
            let rankings = &predictions[idx].1;
            let mut correct: Vec<u32> = rankings.iter()
                .zip(outcomes.iter())
                .filter(|(_, &o)| o == 'y')
                .map(|(r, _)| *r)
                .collect();
            correct.sort_by(|a, b| b.cmp(a));
            (idx, correct)
        })
        .collect();
    
    // Compare level by level
    let max_levels = contestant_rankings.iter()
        .map(|(_, v)| v.len())
        .max()
        .unwrap_or(0);
    
    let mut remaining = tied_indices.to_vec();
    
    for level in 0..max_levels {
        let level_scores: Vec<(usize, u32)> = remaining.iter()
            .map(|&idx| {
                let score = contestant_rankings.iter()
                    .find(|(i, _)| *i == idx)
                    .and_then(|(_, v)| v.get(level))
                    .copied()
                    .unwrap_or(0);
                (idx, score)
            })
            .collect();
        
        let max_score = level_scores.iter().map(|(_, s)| *s).max().unwrap();
        remaining = level_scores.iter()
            .filter(|(_, s)| *s == max_score)
            .map(|(idx, _)| *idx)
            .collect();
        
        if remaining.len() == 1 {
            return remaining[0];
        }
    }
    
    // Still tied - return first alphabetically
    remaining.sort_by(|&a, &b| predictions[a].0.cmp(&predictions[b].0));
    remaining[0]
}

// ============================================================================
// Output formatting
// ============================================================================

fn print_results(data: &GameData, stats: &Stats) {
    let predictions = data.predictions_vec();
    let outcomes = data.outcomes_vec();
    let question_ids = data.question_ids();
    
    let total_possible: u64 = stats.winner_tally.values().sum();
    let total_f = total_possible as f64;

    // Calculate current scores
    let mut current_scores: HashMap<String, u32> = HashMap::new();
    for (name, rankings) in &predictions {
        let score: u32 = rankings.iter()
            .zip(outcomes.iter())
            .filter(|(_, &o)| o == 'y')
            .map(|(r, _)| *r)
            .sum();
        current_scores.insert(name.clone(), score);
    }

    // Sort by percentage descending
    let mut percentages: Vec<_> = stats.winner_tally.iter()
        .map(|(name, count)| (name.clone(), *count as f64 / total_f))
        .collect();
    percentages.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());

    println!("percent of win-paths per person (score so far in parentheses)");
    for (name, pct) in &percentages {
        let score = current_scores.get(name).unwrap_or(&0);
        if *pct == 0.0 {
            println!("{} :  0.0% (eliminated) ({})", name, score);
        } else if *pct < 0.01 {
            println!("{} :  {:.3}% ({})", name, pct * 100.0, score);
        } else {
            println!("{} :  {:.1}% ({})", name, pct * 100.0, score);
        }
    }

    println!("\nTie-breaking Analysis:");
    println!("  - Total tie scenarios before tie-breaking: {} ({:.1}%)", 
             stats.tie_count, stats.tie_count as f64 / total_f * 100.0);
    println!("  - All ties resolved using highest-ranked prediction method");

    // Print win paths for each contestant
    for (name, _) in &percentages {
        let paths = stats.win_paths.get(name).unwrap_or(&0);
        if *paths > 0 {
            println!("Contestant {} has {} ways to win", name, paths);
        }
    }

    // Question 2: per-contestant question analysis
    println!("\n--- Per-contestant question analysis ---");
    
    let maybe_questions: Vec<(usize, String)> = question_ids.iter()
        .enumerate()
        .filter(|(_, qid)| data.outcomes.get(*qid).map(|o| o == "m").unwrap_or(false))
        .map(|(i, qid)| (i, qid.clone()))
        .collect();

    for (name, _pct) in &percentages {
        let paths = *stats.win_paths.get(name).unwrap_or(&0);
        if paths == 0 {
            continue;
        }

        let buckets = stats.person_question_buckets.get(name).unwrap();
        let mut q_percentages: Vec<(String, f64)> = maybe_questions.iter()
            .map(|(idx, qid)| {
                let (y, n) = buckets[*idx];
                let total = y + n;
                let pct = if total > 0 { y as f64 / total as f64 } else { 0.0 };
                (qid.clone(), pct)
            })
            .collect();
        q_percentages.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());

        println!(
            "Contestant {} has {} ways to win, and needs the following to happen (high percentages) or not (low percentages)",
            name, paths
        );
        if let Some((qid, pct)) = q_percentages.first() {
            println!("\t{}: {:.1}%", qid, pct * 100.0);
        }
        if let Some((qid, pct)) = q_percentages.last() {
            println!("\t{}: {:.1}%", qid, pct * 100.0);
        }
    }

    // Question 3: per-question analysis
    println!("\nQuestion 3: for each maybe-question, what happens?");
    
    for (idx, qid) in &maybe_questions {
        println!(
            "Question {} coming TRUE will help (high percentages) or hurt (low percentages) these people",
            qid
        );
        
        let mut person_needs: Vec<(String, f64)> = Vec::new();
        for (name, _) in &percentages {
            let paths = *stats.win_paths.get(name).unwrap_or(&0);
            if paths == 0 {
                continue;
            }
            let buckets = stats.person_question_buckets.get(name).unwrap();
            let (y, n) = buckets[*idx];
            let total = y + n;
            let pct = if total > 0 { y as f64 / total as f64 } else { 0.0 };
            person_needs.push((name.clone(), pct));
        }
        person_needs.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
        
        for (name, pct) in person_needs {
            println!("\t{}: {:.1}%", name, pct * 100.0);
        }
    }

    // Question 4: by yes-count
    println!("\nQuestion 4: who wins, organized by how many more 'yes' outcomes");
    
    for (num_yes, bucket) in stats.yes_buckets.iter().enumerate() {
        if bucket.is_empty() {
            continue;
        }
        println!("If there are {} more yesses, then these people have win-paths:", num_yes);
        
        let mut sorted: Vec<_> = bucket.iter().collect();
        sorted.sort_by(|a, b| b.1.cmp(a.1));
        
        for (name, count) in sorted {
            println!("\t{}: {}", name, count);
        }
    }
}

// ============================================================================
// Main
// ============================================================================

fn main() {
    let args: Vec<String> = std::env::args().collect();
    
    let data_path = if args.len() > 1 {
        args[1].clone()
    } else {
        eprintln!("Usage: {} <data-file.json>", args[0]);
        eprintln!();
        eprintln!("Example:");
        eprintln!("  {} data/2026-test.json   # Fast test (14 unresolved questions)", args[0]);
        eprintln!("  {} data/2026.json        # Full run (26 unresolved)", args[0]);
        eprintln!();
        eprintln!("Data files should be JSON with: year, questions, outcomes, predictions");
        std::process::exit(1);
    };

    println!("Loading data from: {}", data_path);
    
    let data = match GameData::load(&data_path) {
        Ok(d) => d,
        Err(e) => {
            eprintln!("Error loading data: {}", e);
            std::process::exit(1);
        }
    };

    println!("Year: {}", data.year);
    println!("Questions: {}", data.questions.len());
    println!("Contestants: {}", data.predictions.len());

    if let Err(errors) = data.validate() {
        eprintln!("\nValidation errors:");
        for e in errors {
            eprintln!("  - {}", e);
        }
        std::process::exit(1);
    }
    println!("Validation: OK\n");

    let predictions = data.predictions_vec();
    let outcomes = data.outcomes_vec();

    let start = Instant::now();
    let stats = compute_stats(&predictions, &outcomes);
    let duration = start.elapsed();

    let total: u64 = stats.winner_tally.values().sum();
    println!("Computed {} combinations in {:.1}s\n", total, duration.as_secs_f64());

    print_results(&data, &stats);
}

// ============================================================================
// TESTS
// ============================================================================
#[cfg(test)]
mod tests {
    use super::*;

    fn test_predictions() -> Vec<(String, Vec<u32>)> {
        vec![
            ("TEST_A".to_string(), vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
            ("TEST_B".to_string(), vec![10, 9, 8, 7, 6, 5, 4, 3, 2, 1]),
        ]
    }

    #[test]
    fn points_all_yes_sums_all_rankings() {
        let rankings = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
        let outcomes: Vec<char> = vec!['y'; 10];
        assert_eq!(calculate_points(&rankings, &outcomes), 55);
    }

    #[test]
    fn points_all_no_is_zero() {
        let rankings = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
        let outcomes: Vec<char> = vec!['n'; 10];
        assert_eq!(calculate_points(&rankings, &outcomes), 0);
    }

    #[test]
    fn points_only_counts_yes_positions() {
        let rankings = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
        let mut outcomes: Vec<char> = vec!['n'; 10];
        outcomes[0] = 'y';
        outcomes[9] = 'y';
        assert_eq!(calculate_points(&rankings, &outcomes), 11);
    }

    #[test]
    fn stats_total_combinations_correct() {
        let predictions = test_predictions();
        let outcomes: Vec<char> = vec!['m'; 10];
        let stats = compute_stats(&predictions, &outcomes);
        let total: u64 = stats.winner_tally.values().sum();
        assert_eq!(total, 1024);
    }

    #[test]
    fn win_percentages_match_python() {
        let predictions = test_predictions();
        let outcomes: Vec<char> = vec!['m'; 10];
        let stats = compute_stats(&predictions, &outcomes);
        
        let test_a_wins = *stats.winner_tally.get("TEST_A").unwrap();
        let test_b_wins = *stats.winner_tally.get("TEST_B").unwrap();
        
        let pct_a = test_a_wins as f64 / 1024.0 * 100.0;
        let pct_b = test_b_wins as f64 / 1024.0 * 100.0;
        
        assert!((pct_a - 51.6).abs() < 0.1, "TEST_A should be ~51.6%, got {:.1}%", pct_a);
        assert!((pct_b - 48.4).abs() < 0.1, "TEST_B should be ~48.4%, got {:.1}%", pct_b);
    }

    #[test]
    fn tie_scenarios_match_python() {
        let predictions = test_predictions();
        let outcomes: Vec<char> = vec!['m'; 10];
        let stats = compute_stats(&predictions, &outcomes);
        assert_eq!(stats.tie_count, 48);
    }
}
