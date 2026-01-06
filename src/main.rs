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
    /// How many times each contestant wins definitively (no tie, or won tie-breaker)
    pub winner_tally: HashMap<String, u64>,
    /// Scenarios where tie-breaker determined a winner
    pub tie_broken_count: u64,
    /// Scenarios where tie couldn't be broken (true tie, no winner)
    pub true_tie_count: u64,
    /// True ties by yes-count (for debugging)
    pub true_ties_by_yes_count: Vec<u64>,
    /// How many scenarios each contestant could win (had max score, including ties)
    pub win_paths: HashMap<String, u64>,
    /// For each contestant, for each question index: (yes_wins, no_wins)
    pub person_question_buckets: HashMap<String, Vec<(u64, u64)>>,
    /// For each yes-count (0..=num_maybes): count per contestant
    pub yes_buckets: Vec<HashMap<String, u64>>,
    /// For true ties: for each question index, (yes_count, no_count)
    pub true_tie_question_buckets: Vec<(u64, u64)>,
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

        let true_ties_by_yes_count = vec![0; num_maybes + 1];
        let true_tie_question_buckets = vec![(0, 0); num_questions];

        Stats {
            winner_tally,
            tie_broken_count: 0,
            true_tie_count: 0,
            true_ties_by_yes_count,
            win_paths,
            person_question_buckets,
            yes_buckets,
            true_tie_question_buckets,
        }
    }
    
    fn merge(mut self, other: Stats) -> Stats {
        // Merge winner_tally
        for (name, count) in other.winner_tally {
            *self.winner_tally.entry(name).or_insert(0) += count;
        }
        
        // Merge tie counts
        self.tie_broken_count += other.tie_broken_count;
        self.true_tie_count += other.true_tie_count;
        for (i, count) in other.true_ties_by_yes_count.into_iter().enumerate() {
            self.true_ties_by_yes_count[i] += count;
        }
        
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
        
        // Merge true_tie_question_buckets
        for (i, (y, n)) in other.true_tie_question_buckets.into_iter().enumerate() {
            self.true_tie_question_buckets[i].0 += y;
            self.true_tie_question_buckets[i].1 += n;
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
                
                let needs_tiebreaker = winner_indices.len() > 1;
                
                // Determine winner (if any)
                let winner_idx: Option<usize> = if !needs_tiebreaker {
                    Some(winner_indices[0])
                } else {
                    tie_breaker_idx(predictions, &current_outcome, &winner_indices)
                };
                
                // Calculate yes count and more_yesses once
                let yes_count = current_outcome.iter().filter(|&&c| c == 'y').count();
                let more_yesses = yes_count - yesses_already;
                
                // Update all stats based on the actual winner (not all tied contestants)
                match winner_idx {
                    Some(idx) => {
                        let winner_name = &contestants[idx];
                        *stats.winner_tally.get_mut(winner_name).unwrap() += 1;
                        *stats.win_paths.get_mut(winner_name).unwrap() += 1;
                        *stats.yes_buckets[more_yesses].entry(winner_name.clone()).or_insert(0) += 1;
                        
                        if needs_tiebreaker {
                            stats.tie_broken_count += 1;
                        }
                        
                        // Question buckets - only for actual winner
                        if let Some(buckets) = stats.person_question_buckets.get_mut(winner_name) {
                            for (q_idx, &outcome) in current_outcome.iter().enumerate() {
                                if outcome == 'y' {
                                    buckets[q_idx].0 += 1;
                                } else {
                                    buckets[q_idx].1 += 1;
                                }
                            }
                        }
                    }
                    None => {
                        // True tie - no winner
                        stats.true_tie_count += 1;
                        stats.true_ties_by_yes_count[more_yesses] += 1;
                        
                        // Track which questions were yes/no in true tie scenarios
                        for (q_idx, &outcome) in current_outcome.iter().enumerate() {
                            if outcome == 'y' {
                                stats.true_tie_question_buckets[q_idx].0 += 1;
                            } else {
                                stats.true_tie_question_buckets[q_idx].1 += 1;
                            }
                        }
                    }
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
/// Returns Some(winner_idx) if tie was broken, None if true tie (no winner)
fn tie_breaker_idx(
    predictions: &[(String, Vec<u32>)],
    outcomes: &[char],
    tied_indices: &[usize],
) -> Option<usize> {
    if tied_indices.len() == 1 {
        return Some(tied_indices[0]);
    }
    
    // Get each contestant's correct predictions sorted descending
    let contestant_rankings: Vec<(usize, Vec<u32>)> = tied_indices.iter()
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
            return Some(remaining[0]);
        }
    }
    
    // Still tied after all levels - true tie, no winner
    None
}

// ============================================================================
// Output formatting
// ============================================================================

fn print_results(
    data: &GameData, 
    stats: &Stats,
    show_summary: bool,
    show_win_paths: bool,
    show_must_haves: bool,
    show_per_contestant: bool,
    show_per_question: bool,
) {
    let predictions = data.predictions_vec();
    let outcomes = data.outcomes_vec();
    let question_ids = data.question_ids();
    
    // Total scenarios includes true ties (where no one wins)
    let total_with_winners: u64 = stats.winner_tally.values().sum::<u64>();
    let total_scenarios: u64 = total_with_winners + stats.true_tie_count;
    let total_f = total_scenarios as f64;

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

    // Sort by percentage descending (include True Tie as pseudo-participant)
    let mut percentages: Vec<_> = stats.winner_tally.iter()
        .map(|(name, count)| (name.clone(), *count as f64 / total_f))
        .collect();
    // Add True Tie entry
    if stats.true_tie_count > 0 {
        percentages.push(("⚖️ TRUE TIE".to_string(), stats.true_tie_count as f64 / total_f));
    }
    percentages.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());

    // Section: Summary (percentages)
    if show_summary {
        println!("percent of win-paths per person (score so far in parentheses)");
        for (name, pct) in &percentages {
            if name == "⚖️ TRUE TIE" {
                if *pct < 0.01 {
                    println!("{} :  {:.4}% (no winner)", name, pct * 100.0);
                } else {
                    println!("{} :  {:.1}% (no winner)", name, pct * 100.0);
                }
            } else {
                let score = current_scores.get(name).unwrap_or(&0);
                if *pct == 0.0 {
                    println!("{} :  0.0% (eliminated) ({})", name, score);
                } else if *pct < 0.01 {
                    println!("{} :  {:.3}% ({})", name, pct * 100.0, score);
                } else {
                    println!("{} :  {:.1}% ({})", name, pct * 100.0, score);
                }
            }
        }
    }

    // Section: Win paths & tie-breaking
    if show_win_paths {
        let total_ties = stats.tie_broken_count + stats.true_tie_count;
        println!("\nTie-breaking Analysis:");
        println!("  - Scenarios with ties: {} ({:.1}%)", total_ties, total_ties as f64 / total_f * 100.0);
        println!("  - Ties broken (winner determined): {}", stats.tie_broken_count);
        println!("  - True ties (no winner): {}", stats.true_tie_count);

        // Print definitive wins for each contestant (including True Tie)
        for (name, _) in &percentages {
            if name == "⚖️ TRUE TIE" {
                println!("{} has {} scenarios", name, stats.true_tie_count);
            } else {
                let wins = stats.winner_tally.get(name).unwrap_or(&0);
                if *wins > 0 {
                    println!("Contestant {} has {} ways to win", name, wins);
                }
            }
        }
    }

    // Build maybe_questions list once
    let maybe_questions: Vec<(usize, String)> = question_ids.iter()
        .enumerate()
        .filter(|(_, qid)| data.outcomes.get(*qid).map(|o| o == "m").unwrap_or(false))
        .map(|(i, qid)| (i, qid.clone()))
        .collect();

    // Section: Must-Haves & Almost-Must-Haves Analysis
    if show_must_haves {
        println!("\n--- Must-Haves & Almost-Must-Haves ---");
        println!("(Questions where a contestant needs YES ≥95% or NO ≥95% of their win paths)\n");
        
        let mut any_must_haves = false;
        for (name, _pct) in &percentages {
            if name == "⚖️ TRUE TIE" {
                continue;
            }
            let wins = *stats.winner_tally.get(name).unwrap_or(&0);
            if wins == 0 {
                continue;
            }
            
            let buckets = stats.person_question_buckets.get(name).unwrap();
            let mut must_haves: Vec<(String, &str, f64)> = Vec::new();
            
            for (idx, qid) in &maybe_questions {
                let (y, n) = buckets[*idx];
                let total = y + n;
                if total == 0 {
                    continue;
                }
                let pct_yes = y as f64 / total as f64;
                
                if pct_yes >= 0.95 {
                    let label = if pct_yes >= 1.0 { "MUST be YES" } else { "almost must YES" };
                    must_haves.push((qid.clone(), label, pct_yes));
                } else if pct_yes <= 0.05 {
                    let label = if pct_yes <= 0.0 { "MUST be NO" } else { "almost must NO" };
                    must_haves.push((qid.clone(), label, pct_yes));
                }
            }
            
            if !must_haves.is_empty() {
                any_must_haves = true;
                println!("{}:", name);
                for (qid, label, pct) in must_haves {
                    println!("  Q{}: {} ({:.1}% yes)", qid, label, pct * 100.0);
                }
            }
        }
        
        if !any_must_haves {
            println!("No must-haves or almost-must-haves at this stage.");
        }
    }

    // Section: Per-contestant question analysis
    if show_per_contestant {
        println!("\n--- Per-contestant question analysis ---");

        for (name, _pct) in &percentages {
            if name == "⚖️ TRUE TIE" {
                continue;
            }
            let wins = *stats.winner_tally.get(name).unwrap_or(&0);
            if wins == 0 {
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
                name, wins
            );
            if let Some((qid, pct)) = q_percentages.first() {
                println!("\t{}: {:.1}%", qid, pct * 100.0);
            }
            if let Some((qid, pct)) = q_percentages.last() {
                println!("\t{}: {:.1}%", qid, pct * 100.0);
            }
        }
    }

    // Question 3: per-question analysis
    // Section: Per-question analysis
    if show_per_question {
        println!("\n--- Per-question analysis ---");
        println!("For each unresolved question, who benefits if it comes TRUE?\n");

        for (idx, qid) in &maybe_questions {
            println!(
                "Question {} coming TRUE will help (high %) or hurt (low %):",
                qid
            );

            let mut person_needs: Vec<(String, f64)> = Vec::new();
            for (name, _) in &percentages {
                if name == "⚖️ TRUE TIE" {
                    let (y, n) = stats.true_tie_question_buckets[*idx];
                    let total = y + n;
                    let pct = if total > 0 { y as f64 / total as f64 } else { 0.0 };
                    if stats.true_tie_count > 0 {
                        person_needs.push((name.clone(), pct));
                    }
                    continue;
                }
                let wins = *stats.winner_tally.get(name).unwrap_or(&0);
                if wins == 0 {
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
    }

}

fn print_yes_count_buckets(_data: &GameData, stats: &Stats) {
    println!("\n--- Wins by yes-count ---");
    println!("Who wins depending on how many more 'yes' outcomes occur?\n");

    for (num_yes, bucket) in stats.yes_buckets.iter().enumerate() {
        let true_ties_at_level = stats.true_ties_by_yes_count.get(num_yes).copied().unwrap_or(0);
        if bucket.is_empty() && true_ties_at_level == 0 {
            continue;
        }
        println!("If {} more yesses:", num_yes);

        let mut sorted: Vec<(String, u64)> = bucket.iter()
            .map(|(name, count)| (name.clone(), *count))
            .collect();
        if true_ties_at_level > 0 {
            sorted.push(("⚖️ TRUE TIE".to_string(), true_ties_at_level));
        }
        sorted.sort_by(|a, b| b.1.cmp(&a.1));

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
    
    // Parse flags
    let full_mode = args.iter().any(|a| a == "--full");
    let data_args: Vec<&String> = args.iter().skip(1).filter(|a| !a.starts_with("--")).collect();
    
    let data_path = if !data_args.is_empty() {
        data_args[0].clone()
    } else {
        eprintln!("Usage: {} <data-file.json> [--full]", args[0]);
        eprintln!();
        eprintln!("Options:");
        eprintln!("  --full    Show all output (no interactive menu)");
        eprintln!();
        eprintln!("Example:");
        eprintln!("  {} data/2026-test.json        # Interactive mode", args[0]);
        eprintln!("  {} data/2026.json --full      # Full output", args[0]);
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

    let winners_determined: u64 = stats.winner_tally.values().sum::<u64>();
    let total_scenarios: u64 = winners_determined + stats.true_tie_count;
    println!("Computed {} scenarios in {:.1}s ({} with definitive winner, {} true ties)\n", 
             total_scenarios, duration.as_secs_f64(),
             winners_determined,
             stats.true_tie_count);

    if full_mode {
        print_results(&data, &stats, true, true, true, true, true);
    } else {
        // Always show summary
        print_results(&data, &stats, true, false, false, false, false);
        
        // Interactive menu
        println!("\n--- View more details ---");
        println!("  1) Win paths & tie-breaking analysis");
        println!("  2) Must-haves & almost-must-haves");
        println!("  3) Per-contestant question analysis");
        println!("  4) Per-question analysis");
        println!("  5) Wins by yes-count");
        println!("  q) Quit");
        println!();
        
        use std::io::{self, BufRead, Write};
        let stdin = io::stdin();
        loop {
            print!("> ");
            io::stdout().flush().unwrap();
            
            let mut line = String::new();
            if stdin.lock().read_line(&mut line).is_err() {
                break;
            }
            
            match line.trim() {
                "1" => print_results(&data, &stats, false, true, false, false, false),
                "2" => print_results(&data, &stats, false, false, true, false, false),
                "3" => print_results(&data, &stats, false, false, false, true, false),
                "4" => print_results(&data, &stats, false, false, false, false, true),
                "5" => print_yes_count_buckets(&data, &stats),
                "q" | "Q" | "" => break,
                _ => println!("Unknown option. Enter 1-5 or q to quit."),
            }
        }
    }
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
        // Total = winners + true ties
        let total: u64 = stats.winner_tally.values().sum::<u64>() + stats.true_tie_count;
        assert_eq!(total, 1024);
    }

    #[test]
    fn symmetric_predictions_have_true_ties() {
        // TEST_A and TEST_B are perfect inverses, so some scenarios are true ties
        let predictions = test_predictions();
        let outcomes: Vec<char> = vec!['m'; 10];
        let stats = compute_stats(&predictions, &outcomes);
        
        // With symmetric predictions, true ties occur when both have same sorted rankings
        assert!(stats.true_tie_count > 0, "Symmetric predictions should produce true ties");
        
        // Winners should be equal (symmetry)
        let test_a_wins = *stats.winner_tally.get("TEST_A").unwrap();
        let test_b_wins = *stats.winner_tally.get("TEST_B").unwrap();
        assert_eq!(test_a_wins, test_b_wins, "Symmetric predictions should have equal wins");
    }

    #[test]
    fn tie_scenarios_match_python() {
        let predictions = test_predictions();
        let outcomes: Vec<char> = vec!['m'; 10];
        let stats = compute_stats(&predictions, &outcomes);
        // Total ties = broken + true ties
        let total_ties = stats.tie_broken_count + stats.true_tie_count;
        assert_eq!(total_ties, 48);
    }
}
