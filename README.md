# Prediction Game

Calculates win probabilities for a prediction game where contestants rank questions by likelihood.

## Rust version

Fast implementation for computing all 2^N possible outcomes.

### Build & Run

```bash
cargo build --release
./target/release/prediction_game
```

### Configure number of questions

```bash
NUM_Q=20 ./target/release/prediction_game
```

### Run tests

```bash
cargo test
```

### Performance

| Questions | Combinations | Time (release) |
|-----------|--------------|----------------|
| 10        | 1K           | 0.001s         |
| 20        | 1M           | 0.6s           |
| 22        | 4M           | 2.9s           |
| 26        | 67M          | ~46s (est.)    |

## Python version

Original implementation in `prediction-possibilities-2026.py`.

```bash
# Test mode (10 questions)
TEST_MODE=1 python3 prediction-possibilities-2026.py
```
