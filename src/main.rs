use std::collections::HashMap;
use std::time::Instant;

#[derive(Debug, Clone)]
struct WinInfo {
    winner: String,
    was_tie: bool,
    tied_contestants: Vec<String>,
}

fn main() {
    // Test data: configurable number of questions
    let num_questions: usize = std::env::var("NUM_Q")
        .ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or(10);
    
    let predictions: Vec<(&str, Vec<u32>)> = vec![
        ("TEST_A", (1..=num_questions as u32).collect()),
        ("TEST_B", (1..=num_questions as u32).rev().collect()),
    ];
    let outcomes: Vec<char> = vec!['m'; num_questions]; // all maybes
    
    let start = Instant::now();
    let results = compute_all_outcomes(&predictions, &outcomes);
    let duration = start.elapsed();
    
    println!("Hot loop took {:.3}s for {} combinations", 
             duration.as_secs_f64(), results.len());
    
    // Tally winners
    let mut winner_tally: HashMap<String, u32> = HashMap::new();
    for (name, _) in &predictions {
        winner_tally.insert(name.to_string(), 0);
    }
    
    let mut tie_scenarios = 0;
    for win_info in results.values() {
        *winner_tally.get_mut(&win_info.winner).unwrap() += 1;
        if win_info.was_tie {
            tie_scenarios += 1;
        }
    }
    
    let total_possible = results.len() as f64;
    
    // Sort by percentage descending
    let mut percentages: Vec<_> = winner_tally.iter()
        .map(|(name, count)| (name.clone(), *count as f64 / total_possible))
        .collect();
    percentages.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
    
    println!("percent of win-paths per person (score so far in parentheses)");
    for (name, pct) in &percentages {
        // Current score is 0 since all outcomes are "m"
        println!("{} :  {:.1}% (0)", name, pct * 100.0);
    }
    
    println!("\nTie-breaking Analysis:");
    println!("  - Total tie scenarios before tie-breaking: {} ({:.1}%)", 
             tie_scenarios, tie_scenarios as f64 / total_possible * 100.0);
    println!("  - All ties resolved using highest-ranked prediction method");
    
    // Count win paths per contestant (includes ties where they participated)
    let mut win_paths: HashMap<String, u32> = HashMap::new();
    for (name, _) in &predictions {
        win_paths.insert(name.to_string(), 0);
    }
    for win_info in results.values() {
        for contestant in &win_info.tied_contestants {
            *win_paths.get_mut(contestant).unwrap() += 1;
        }
    }
    
    for (name, _) in &predictions {
        let paths = win_paths.get(*name).unwrap();
        println!("Contestant {} has {} ways to win", name, paths);
    }
}

fn compute_all_outcomes(
    predictions: &[(&str, Vec<u32>)],
    outcomes: &[char],
) -> HashMap<String, WinInfo> {
    let mut results = HashMap::new();
    
    // Find unresolved (maybe) indices
    let unresolved_indices: Vec<usize> = outcomes.iter()
        .enumerate()
        .filter(|(_, &o)| o == 'm')
        .map(|(i, _)| i)
        .collect();
    
    let num_unresolved = unresolved_indices.len();
    let total_combinations = 1u64 << num_unresolved;
    
    for i in 0..total_combinations {
        // Build outcome string
        let mut current_outcome: Vec<char> = outcomes.iter()
            .map(|&o| if o == 'y' { 'y' } else if o == 'n' { 'n' } else { '_' })
            .collect();
        
        for (bit_pos, &idx) in unresolved_indices.iter().enumerate() {
            current_outcome[idx] = if (i >> bit_pos) & 1 == 1 { 'y' } else { 'n' };
        }
        
        let outcome_str: String = current_outcome.iter().collect();
        
        // Calculate points for each contestant
        let scores: Vec<(String, u32)> = predictions.iter()
            .map(|(name, rankings)| {
                let pts = calculate_points(rankings, &current_outcome);
                (name.to_string(), pts)
            })
            .collect();
        
        let max_score = scores.iter().map(|(_, s)| *s).max().unwrap();
        let possible_winners: Vec<String> = scores.iter()
            .filter(|(_, s)| *s == max_score)
            .map(|(name, _)| name.clone())
            .collect();
        
        let (winner, was_tie) = if possible_winners.len() == 1 {
            (possible_winners[0].clone(), false)
        } else {
            let winner = tie_breaker(predictions, &current_outcome, &possible_winners);
            (winner, true)
        };
        
        results.insert(outcome_str, WinInfo {
            winner,
            was_tie,
            tied_contestants: possible_winners,
        });
    }
    
    results
}

fn calculate_points(rankings: &[u32], outcomes: &[char]) -> u32 {
    rankings.iter()
        .zip(outcomes.iter())
        .filter(|(_, &o)| o == 'y')
        .map(|(r, _)| *r)
        .sum()
}

fn tie_breaker(
    predictions: &[(&str, Vec<u32>)],
    outcomes: &[char],
    tied_contestants: &[String],
) -> String {
    if tied_contestants.len() == 1 {
        return tied_contestants[0].clone();
    }
    
    // Get each contestant's correct predictions sorted descending
    let mut contestant_rankings: HashMap<String, Vec<u32>> = HashMap::new();
    
    for name in tied_contestants {
        let rankings = predictions.iter()
            .find(|(n, _)| *n == name)
            .map(|(_, r)| r)
            .unwrap();
        
        let mut correct: Vec<u32> = rankings.iter()
            .zip(outcomes.iter())
            .filter(|(_, &o)| o == 'y')
            .map(|(r, _)| *r)
            .collect();
        correct.sort_by(|a, b| b.cmp(a)); // descending
        contestant_rankings.insert(name.clone(), correct);
    }
    
    // Compare level by level
    let max_levels = contestant_rankings.values()
        .map(|v| v.len())
        .max()
        .unwrap_or(0);
    
    let mut remaining: Vec<String> = tied_contestants.to_vec();
    
    for level in 0..max_levels {
        let level_scores: Vec<(String, u32)> = remaining.iter()
            .map(|name| {
                let score = contestant_rankings.get(name)
                    .and_then(|v| v.get(level))
                    .copied()
                    .unwrap_or(0);
                (name.clone(), score)
            })
            .collect();
        
        let max_score = level_scores.iter().map(|(_, s)| *s).max().unwrap();
        remaining = level_scores.iter()
            .filter(|(_, s)| *s == max_score)
            .map(|(n, _)| n.clone())
            .collect();
        
        if remaining.len() == 1 {
            return remaining[0].clone();
        }
    }
    
    // Still tied - return first alphabetically
    remaining.sort();
    remaining[0].clone()
}

// ============================================================================
// TESTS - Human readable, matching Python behavior
// ============================================================================
#[cfg(test)]
mod tests {
    use super::*;

    fn test_predictions() -> Vec<(&'static str, Vec<u32>)> {
        vec![
            ("TEST_A", vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
            ("TEST_B", vec![10, 9, 8, 7, 6, 5, 4, 3, 2, 1]),
        ]
    }

    // --- Points calculation ---
    
    #[test]
    fn points_all_yes_sums_all_rankings() {
        // TEST_A ranks questions 1-10, all "yes" = 1+2+...+10 = 55
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
        // Only positions 0 and 9 are "yes"
        let rankings = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
        let mut outcomes: Vec<char> = vec!['n'; 10];
        outcomes[0] = 'y'; // ranking 1
        outcomes[9] = 'y'; // ranking 10
        assert_eq!(calculate_points(&rankings, &outcomes), 11); // 1 + 10
    }

    // --- Winner determination ---

    #[test]
    fn test_a_wins_when_low_questions_are_yes() {
        // TEST_A: [1,2,3,4,5,6,7,8,9,10] - low numbers on early questions
        // TEST_B: [10,9,8,7,6,5,4,3,2,1] - high numbers on early questions
        // If only question A (index 0) is yes: TEST_A gets 1, TEST_B gets 10
        // TEST_B wins
        let predictions = test_predictions();
        let outcomes: Vec<char> = "ynnnnnnnnn".chars().collect();
        let results = compute_all_outcomes(&predictions, &outcomes);
        
        assert_eq!(results.len(), 1); // only one possible outcome
        let win_info = results.values().next().unwrap();
        assert_eq!(win_info.winner, "TEST_B");
    }

    #[test]
    fn test_a_wins_when_high_questions_are_yes() {
        // If only question J (index 9) is yes: TEST_A gets 10, TEST_B gets 1
        // TEST_A wins
        let predictions = test_predictions();
        let outcomes: Vec<char> = "nnnnnnnnny".chars().collect();
        let results = compute_all_outcomes(&predictions, &outcomes);
        
        let win_info = results.values().next().unwrap();
        assert_eq!(win_info.winner, "TEST_A");
    }

    // --- Tie scenarios ---

    #[test]
    fn tie_when_same_total_points() {
        // Questions A and J both yes: 
        // TEST_A: 1 + 10 = 11
        // TEST_B: 10 + 1 = 11
        // Tie! Winner determined by tie-breaker (highest single correct prediction)
        // TEST_A has 10, TEST_B has 10 -> still tied -> alphabetical: TEST_A wins
        let predictions = test_predictions();
        let outcomes: Vec<char> = "ynnnnnnnny".chars().collect();
        let results = compute_all_outcomes(&predictions, &outcomes);
        
        let win_info = results.values().next().unwrap();
        assert!(win_info.was_tie, "Should be a tie scenario");
        assert_eq!(win_info.winner, "TEST_A", "Alphabetically first wins perfect tie");
    }

    // --- Full simulation stats (matching Python TEST_MODE output) ---

    #[test]
    fn total_combinations_is_1024_for_10_maybes() {
        let predictions = test_predictions();
        let outcomes: Vec<char> = vec!['m'; 10];
        let results = compute_all_outcomes(&predictions, &outcomes);
        assert_eq!(results.len(), 1024); // 2^10
    }

    #[test]
    fn win_percentages_match_python() {
        // Python output: TEST_A: 51.6%, TEST_B: 48.4%
        let predictions = test_predictions();
        let outcomes: Vec<char> = vec!['m'; 10];
        let results = compute_all_outcomes(&predictions, &outcomes);
        
        let mut test_a_wins = 0;
        let mut test_b_wins = 0;
        for win_info in results.values() {
            match win_info.winner.as_str() {
                "TEST_A" => test_a_wins += 1,
                "TEST_B" => test_b_wins += 1,
                _ => {}
            }
        }
        
        let pct_a = test_a_wins as f64 / 1024.0 * 100.0;
        let pct_b = test_b_wins as f64 / 1024.0 * 100.0;
        
        // Allow small rounding difference
        assert!((pct_a - 51.6).abs() < 0.1, "TEST_A should be ~51.6%, got {:.1}%", pct_a);
        assert!((pct_b - 48.4).abs() < 0.1, "TEST_B should be ~48.4%, got {:.1}%", pct_b);
    }

    #[test]
    fn tie_scenarios_match_python() {
        // Python output: 48 tie scenarios (4.7%)
        let predictions = test_predictions();
        let outcomes: Vec<char> = vec!['m'; 10];
        let results = compute_all_outcomes(&predictions, &outcomes);
        
        let ties = results.values().filter(|w| w.was_tie).count();
        assert_eq!(ties, 48, "Should have exactly 48 tie scenarios");
    }

    #[test]
    fn each_contestant_has_536_win_paths() {
        // Python: "TEST_A has 536 ways to win" (including ties where they win tiebreaker)
        // Python: "TEST_B has 536 ways to win"
        let predictions = test_predictions();
        let outcomes: Vec<char> = vec!['m'; 10];
        let results = compute_all_outcomes(&predictions, &outcomes);
        
        // Count scenarios where each contestant is involved (winner or tied)
        let mut test_a_paths = 0;
        let mut test_b_paths = 0;
        for win_info in results.values() {
            if win_info.tied_contestants.contains(&"TEST_A".to_string()) {
                test_a_paths += 1;
            }
            if win_info.tied_contestants.contains(&"TEST_B".to_string()) {
                test_b_paths += 1;
            }
        }
        
        assert_eq!(test_a_paths, 536, "TEST_A should have 536 win paths");
        assert_eq!(test_b_paths, 536, "TEST_B should have 536 win paths");
    }
}

