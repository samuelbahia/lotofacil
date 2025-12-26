# Lottery Analysis System - Usage Guide

## Quick Start

### 1. Setup

First, ensure you have Python 3.11+ installed and install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Import Existing Data

If you have existing lottery data in CSV format (like `base/resultados.csv`), import it:

```bash
python migrate_data.py
```

This will create a SQLite database at `base/lottery_data.db` with all historical data.

### 3. Run the System

#### Option A: Interactive Dashboard

Launch the Streamlit dashboard for a visual interface:

```bash
streamlit run app.py
```

Then open your browser to `http://localhost:8501`

#### Option B: Command-Line Interface

Use the CLI for quick operations:

```bash
# Show help
python main.py --help

# Quick play (update, analyze, generate games)
python main.py --quick-play --lottery lotofacil

# Show statistics
python main.py --stats --lottery lotofacil

# Analyze patterns
python main.py --analyze --lottery lotofacil

# Generate games
python main.py --generate-games --lottery lotofacil --count 10 --strategy balanced
```

## Common Workflows

### Workflow 1: Daily Game Generation

1. Check database stats:
   ```bash
   python main.py --stats --lottery lotofacil
   ```

2. Analyze recent patterns:
   ```bash
   python main.py --analyze --lottery lotofacil --output today_analysis.json
   ```

3. Generate games:
   ```bash
   python main.py --generate-games --lottery lotofacil --count 6 --output my_games.txt
   ```

### Workflow 2: ML-Enhanced Analysis

1. Train Random Forest model:
   ```bash
   python ml_models.py --lottery lotofacil --train-rf
   ```

2. Perform clustering:
   ```bash
   python ml_models.py --lottery lotofacil --cluster
   ```

3. Get predictions:
   ```bash
   python ml_models.py --lottery lotofacil --predict --output predictions.json
   ```

### Workflow 3: Compare Strategies

Generate games with different strategies and compare:

```bash
python main.py --generate-games --lottery megasena --count 10 --strategy conservative --output conservative_games.txt
python main.py --generate-games --lottery megasena --count 10 --strategy aggressive --output aggressive_games.txt
python main.py --generate-games --lottery megasena --count 10 --strategy balanced --output balanced_games.txt
```

## Configuration

Edit `config.yaml` to customize:

### Enable/Disable Lotteries

```yaml
lotteries:
  lotofacil:
    enabled: true
  megasena:
    enabled: true
  quina:
    enabled: false  # Disable if not needed
```

### Adjust Strategy Weights

```yaml
strategies:
  balanced:
    weight_hot_numbers: 0.4      # Increase to favor hot numbers
    weight_cold_numbers: 0.3     # Increase to favor cold numbers
    weight_frequency: 0.3        # Overall frequency weight
    distribute_quadrants: true   # Ensure quadrant coverage
    target_average_sum: true     # Target average sum
```

### ML Settings

```yaml
machine_learning:
  enabled: true
  models:
    random_forest:
      enabled: true
      n_estimators: 100    # Number of trees
      max_depth: 10        # Tree depth
    kmeans:
      enabled: true
      n_clusters: 5        # Number of clusters
```

## Advanced Features

### Custom Analysis

Create custom analysis scripts using the modules:

```python
from data_collector import DataCollector
from statistical_analysis import StatisticalAnalysis

# Load data
collector = DataCollector()
df = collector.get_lottery_data('lotofacil')

# Analyze
analyzer = StatisticalAnalysis()
freq = analyzer.calculate_frequency(df, 'lotofacil')
hot_cold = analyzer.identify_hot_cold_numbers(df, 'lotofacil')

print(f"Hot numbers: {hot_cold['hot_numbers']}")
```

### Backtesting

Test strategies on historical data:

```python
from ml_models import LotteryMLModels
from game_generator import GameGenerator

ml = LotteryMLModels()
generator = GameGenerator()

# Define strategy function
def my_strategy(df, lottery_type):
    return generator.generate_balanced_game(df, lottery_type)

# Backtest
results = ml.backtest_strategy(df, 'lotofacil', my_strategy, n_draws=100)
print(f"ROI: {results['roi_percentage']:.2f}%")
```

## Troubleshooting

### "No data found" error

**Solution**: Run the migration script first:
```bash
python migrate_data.py
```

### "Module not found" error

**Solution**: Install all dependencies:
```bash
pip install -r requirements.txt
```

### Slow performance

**Solutions**:
- Reduce number of games generated
- Reduce analysis period (e.g., last 100 draws instead of all)
- Disable ML features in config if not needed

### Database locked error

**Solution**: Close any other programs accessing the database, then try again.

## Performance Optimization

### For Large Datasets

1. **Use indexes**: The database automatically creates indexes on key fields
2. **Limit queries**: Use the `limit` parameter when loading data
3. **Cache results**: Save analysis results to JSON and reuse

### For Game Generation

1. **Parallel generation**: Generate games in batches
2. **Adjust validation**: Reduce `max_attempts` in code if needed
3. **Strategy selection**: Use single strategy instead of 'all'

## Best Practices

### 1. Regular Updates

Keep your database current:
```bash
# Set up a cron job or scheduled task
python main.py --update
```

### 2. Track Results

Save generated games and track results:
```bash
python main.py --generate-games --lottery lotofacil --output games_$(date +%Y%m%d).txt
```

### 3. Diversify Strategies

Don't rely on a single strategy. Use mix of:
- Conservative (40%)
- Balanced (40%)
- Aggressive (20%)

### 4. Budget Management

Set a budget and stick to it:
- Calculate total cost before playing
- Use intermediate strategy for better ROI on smaller prizes
- Don't chase losses

### 5. Analyze Before Playing

Always run analysis before generating games:
```bash
python main.py --analyze --lottery lotofacil
python main.py --generate-games --lottery lotofacil
```

## Output Files

### JSON Format

Analysis and games can be saved as JSON for programmatic access:

```json
{
  "game_id": 1,
  "strategy": "balanced",
  "numbers": [1, 2, 3, 5, 7, 9, 11, 13, 15, 17, 19, 20, 22, 24, 25],
  "cost": 2.50
}
```

### Text Format

Human-readable format for printing or manual entry:

```
Game #01 [BALANCED    ] R$    2.50
  Numbers: 01 02 03 05 07 09 11 13 15 17 19 20 22 24 25
```

## Dashboard Features

### Statistics Page

- Number frequency charts
- Hot/cold number indicators
- Even/odd distribution
- Correlation heatmaps
- Top pairs analysis

### Generate Games Page

- Interactive game generation
- Strategy selection
- Download options (JSON/Text)
- Investment calculator

### ML Insights Page

- K-means clustering
- Random Forest training
- Pattern recognition
- Cluster visualization

## Support

For issues or questions:
1. Check this guide
2. Review the main README
3. Check inline documentation (docstrings)
4. Open an issue on GitHub

## Legal Notice

This software is for **educational purposes only**. The developers:
- Do not guarantee any wins
- Are not responsible for any losses
- Recommend responsible gaming
- Advise playing within your means

Lottery games are games of chance. Play responsibly.
