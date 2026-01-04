#!/usr/bin/env python3
"""
Wisdom of the Crowds Generator

Takes a prediction game JSON file and adds a "WISCROWD🧠" contestant
whose rankings are derived from the collective wisdom of all contestants.

Algorithm:
  For each question, compute the mean ranking across all contestants.
  Then rank these means: lowest mean gets rank 1 (crowd bets NO),
  highest mean gets rank 26 (crowd bets YES).

This ensures valid rankings (1-26, no duplicates) while capturing
the collective sentiment about which predictions are most/least likely.
"""

import json
import sys
from statistics import mean


def compute_wiscrowd_rankings(predictions: dict) -> list[int]:
    """
    Compute WISCROWD rankings from all contestants' predictions.
    
    Returns a list of rankings (1-26) for each question.
    """
    # Get all contestants' rankings as lists
    all_rankings = list(predictions.values())
    num_questions = len(all_rankings[0])
    
    # For each question, compute mean ranking across all contestants
    mean_rankings = []
    for q_idx in range(num_questions):
        q_mean = mean(rankings[q_idx] for rankings in all_rankings)
        mean_rankings.append((q_idx, q_mean))
    
    # Sort by mean (higher mean = crowd thinks it WILL happen = deserves more points)
    mean_rankings.sort(key=lambda x: x[1])
    
    # Assign ranks: lowest mean gets rank 1, highest mean gets rank 26
    # This mirrors the crowd's confidence
    wiscrowd = [0] * num_questions
    for rank, (q_idx, _mean) in enumerate(mean_rankings, start=1):
        wiscrowd[q_idx] = rank
    
    return wiscrowd


def main():
    if len(sys.argv) < 2:
        print("Usage: python wiscrowd.py <input.json> [output.json]")
        print()
        print("Adds WISCROWD🧠 contestant based on mean rankings.")
        print("If output.json not specified, prints to stdout.")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Load data
    with open(input_path) as f:
        data = json.load(f)
    
    # Compute WISCROWD rankings
    wiscrowd = compute_wiscrowd_rankings(data["predictions"])
    
    # Show the algorithm's work
    print("WISCROWD🧠 Rankings (by mean confidence):", file=sys.stderr)
    print("-" * 50, file=sys.stderr)
    
    questions = data["questions"]
    all_rankings = list(data["predictions"].values())
    
    # Compute and display means with resulting ranks
    means_with_info = []
    for q_idx, qid in enumerate(questions):
        q_mean = mean(rankings[q_idx] for rankings in all_rankings)
        means_with_info.append((qid, q_mean, wiscrowd[q_idx]))
    
    # Sort by WISCROWD rank to show in order of confidence
    means_with_info.sort(key=lambda x: x[2])
    
    for qid, q_mean, rank in means_with_info:
        confidence = "YES" if rank > len(questions) // 2 else "NO"
        print(f"  Rank {rank:2d}: {qid} (mean={q_mean:.1f}) → betting {confidence}", file=sys.stderr)
    
    # Add WISCROWD to predictions
    data["predictions"]["WISCROWD🧠"] = wiscrowd
    
    # Output
    output_json = json.dumps(data, indent=2)
    
    if output_path:
        with open(output_path, 'w') as f:
            f.write(output_json)
        print(f"\nWrote {output_path} with WISCROWD🧠 added", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
