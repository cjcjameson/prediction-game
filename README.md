# Prediction Game

Calculates win probabilities for a prediction game where contestants rank 26 questions by likelihood (1-26). Points are awarded based on rankings for questions that come true.

## Quick Start

```bash
# Build
cargo build --release

# Run with test data (fast - 14 unresolved questions)
./target/release/prediction_game data/2026-test.json

# Run with full 2026 data (slow - 26 unresolved = 67M combinations)
./target/release/prediction_game data/2026.json
```

## Project Structure

```
├── data/
│   ├── 2026.json       # Full 2026 predictions (17 contestants, 26 questions)
│   └── 2026-test.json  # Test scenario (5 contestants, 14 unresolved)
├── src/
│   └── main.rs         # All Rust code (loading, validation, computation, output)
├── archive/            # Historical Python scripts by year
└── prediction-possibilities-2026.py  # Original Python implementation
```

## Data Format (JSON)

```json
{
  "year": 2026,
  "questions": { "A": "Description...", ... },
  "outcomes": { "A": "m", "B": "y", "C": "n", ... },
  "predictions": {
    "PlayerName": [22, 7, 8, ...],  // rankings for A, B, C, ... (1-26)
    ...
  }
}
```

Outcomes: `"y"` = yes (happened), `"n"` = no, `"m"` = maybe (unresolved)

## Running Tests

```bash
cargo test
```
