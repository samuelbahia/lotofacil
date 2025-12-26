# Complete Lottery Analysis System

A comprehensive Python-based system for statistical analysis and intelligent game generation for Brazilian lottery games (Lotofácil, Mega-Sena, Quina, and more).

## 🎯 Features

### Data Collection & Management
- **Automated data collection** from official Caixa Econômica Federal sources
- **SQLite database** for efficient data storage and retrieval
- **Data validation** with checksums to ensure integrity
- **Migration tools** to import existing data
- Support for multiple lottery types

### Statistical Analysis
- **Frequency analysis**: Identify hot and cold numbers
- **Pattern detection**: Consecutive sequences, even/odd distribution, prime numbers
- **Correlation analysis**: Co-occurrence matrices, frequent pairs and triplets
- **Cycle analysis**: Time between number appearances
- **Temporal analysis**: Patterns by day, month, and year
- **Chi-square test**: Verify randomness of distributions
- **Quadrant distribution**: Analyze number distribution across card layout
- **Sum statistics**: Analyze sum ranges of winning combinations

### Intelligent Game Generation
Multiple strategies to maximize winning chances:

- **Conservative Strategy**: Focus on most frequent numbers with balanced distribution
- **Aggressive Strategy**: Mix of hot and cold numbers for coverage
- **Balanced Strategy**: Optimal distribution across all statistical factors
- **Intermediate Strategy**: Focus on secondary prizes (14/15 points in Lotofácil)

Features:
- Smart number weighting based on multiple factors
- Game validation to avoid obvious patterns
- Diversification across multiple games
- Cost calculation and ROI tracking

### Command-Line Interface
Easy-to-use CLI for all operations:
- Update lottery data
- Perform statistical analysis
- Generate games with different strategies
- Export results to JSON/text files

## 📋 Requirements

- Python 3.11+
- Dependencies listed in `requirements.txt`

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/samuelbahia/lotofacil.git
cd lotofacil
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) If you have existing data, migrate it:
```bash
python migrate_data.py
```

## 💻 Usage

### Quick Start

The easiest way to get started is with the quick-play mode:

```bash
python main.py --quick-play --lottery lotofacil
```

This will:
1. Update data (if available)
2. Show database statistics
3. Analyze patterns
4. Generate 6 games using all strategies

### Individual Commands

#### Update Lottery Data

Update all enabled lotteries:
```bash
python main.py --update
```

Update specific lottery:
```bash
python main.py --update --lottery lotofacil
```

#### Show Statistics

```bash
python main.py --stats --lottery lotofacil
```

Output:
```
============================================================
LOTOFACIL - DATABASE STATISTICS
============================================================
  Total draws in database: 1991
  Latest draw number: #1991
  Latest draw date: 2020-10-07
============================================================
```

#### Perform Statistical Analysis

Basic analysis:
```bash
python main.py --analyze --lottery lotofacil
```

Save full report to file:
```bash
python main.py --analyze --lottery lotofacil --output analysis_report.json
```

Output includes:
- Top 10 most frequent numbers
- Hot and cold numbers
- Even/odd distribution patterns
- Sum statistics
- Top number pairs and triplets
- Chi-square randomness test
- And much more...

#### Generate Games

Generate 10 games with all strategies:
```bash
python main.py --generate-games --lottery lotofacil --count 10
```

Generate with specific strategy:
```bash
python main.py --generate-games --lottery megasena --count 6 --strategy conservative
```

Save games to file:
```bash
python main.py --generate-games --lottery quina --count 10 --output my_games.txt
```

Available strategies:
- `conservative`: Most frequent numbers with balance
- `aggressive`: Mix of hot and cold numbers
- `balanced`: Optimal distribution (recommended)
- `intermediate`: Focus on secondary prizes
- `all`: Mix of all strategies (default)

### Supported Lotteries

Currently supported:
- **Lotofácil** ✅ (fully tested)
- **Mega-Sena** ✅ (configured)
- **Quina** ✅ (configured)
- **Lotomania** ⚠️ (configured, needs testing)

## 📊 Example Output

### Statistical Analysis

```
============================================================
LOTOFACIL - STATISTICAL ANALYSIS
============================================================

Total draws analyzed: 1991

TOP 10 MOST FREQUENT NUMBERS:
   1. Number 13: 1234 times (62.0%)
   2. Number 24: 1229 times (61.7%)
   3. Number 10: 1228 times (61.7%)
   ...

HOT NUMBERS (Recent): [10, 23, 16, 4, 9, 5, 20, 2, 12, 3]
COLD NUMBERS (Recent): [7, 19, 25, 14, 17, 11, 8, 18, 1, 21]

EVEN/ODD DISTRIBUTION:
  Average Even: 7.2
  Average Odd: 7.8
  Most Common: [((7, 8), 625), ((8, 7), 504)]

TOP 5 NUMBER PAIRS:
  1. (13, 20): 746 times
  2. (4, 24): 740 times
  3. (13, 24): 740 times
  ...

RANDOMNESS TEST (Chi-Square):
  p-value: 0.9791
  Interpretation: Distribution appears random
```

### Game Generation

```
============================================================
LOTOFACIL - Generated Games
============================================================

Game #01 [BALANCED    ] R$    2.50
  Numbers: 01 02 03 06 07 08 10 12 13 14 16 20 21 22 25

Game #02 [BALANCED    ] R$    2.50
  Numbers: 02 04 05 08 09 11 12 13 15 16 17 20 23 24 25

Game #03 [BALANCED    ] R$    2.50
  Numbers: 01 02 03 04 07 09 10 11 12 15 19 20 21 23 24

...

============================================================
Total Games: 6
Total Investment: R$ 15.00
Strategy Distribution: {'balanced': 6}
============================================================
```

## 🏗️ Project Structure

```
lotofacil/
├── main.py                    # Main CLI entry point
├── data_collector.py          # Data collection and database management
├── statistical_analysis.py    # Statistical analysis module
├── game_generator.py          # Intelligent game generation
├── migrate_data.py           # Migration utility for existing data
├── config.yaml               # Configuration file
├── requirements.txt          # Python dependencies
├── base/                     # Data directory
│   ├── lottery_data.db      # SQLite database (auto-created)
│   └── resultados.csv       # Legacy CSV data
└── logs/                     # Log files (auto-created)
```

## ⚙️ Configuration

Edit `config.yaml` to customize:

- **Database settings**: SQLite or PostgreSQL
- **Lottery configurations**: Enable/disable specific lotteries
- **Analysis parameters**: Frequency windows, correlation thresholds
- **Strategy weights**: Customize game generation strategies
- **Game generation**: Number of games, cost limits
- **Logging**: Log levels and output

Example configuration:
```yaml
strategies:
  balanced:
    weight_hot_numbers: 0.4
    weight_cold_numbers: 0.3
    weight_frequency: 0.3
    distribute_quadrants: true
    target_average_sum: true
```

## 🔍 Module Details

### Data Collector (`data_collector.py`)

Handles:
- Downloading data from official APIs
- SQLite database management
- Data validation and deduplication
- Checksum verification

Key features:
- Automatic retry on download failures
- Support for multiple lottery formats
- Efficient database queries with proper indexing

### Statistical Analysis (`statistical_analysis.py`)

Provides comprehensive analysis:
- Frequency calculations (absolute and relative)
- Hot/cold number identification
- Moving averages
- Cycle analysis (time between appearances)
- Pattern detection (sequences, even/odd, primes)
- Correlation matrices
- Statistical tests (chi-square)

### Game Generator (`game_generator.py`)

Intelligent game generation:
- Multiple strategies based on statistical analysis
- Number weighting system
- Game validation (avoid obvious patterns)
- Diversification across multiple games
- Cost calculation

## 🎓 Statistical Strategies Explained

### Conservative Strategy
- **Weight**: 70% hot numbers, 10% cold numbers, 20% overall frequency
- **Focus**: Most reliable patterns from history
- **Best for**: Risk-averse players seeking consistent results
- **Balance**: Ensures even/odd distribution

### Aggressive Strategy
- **Weight**: 50% hot numbers, 30% cold numbers, 20% frequency
- **Focus**: Coverage of statistical extremes
- **Best for**: Players willing to take calculated risks
- **Balance**: Allows more extreme patterns

### Balanced Strategy (Recommended)
- **Weight**: 40% hot numbers, 30% cold numbers, 30% frequency
- **Focus**: Optimal distribution across all factors
- **Best for**: Most players - balances probability with coverage
- **Features**: Quadrant distribution, target sum ranges

### Intermediate Strategy
- **Focus**: Maximizing chances for secondary prizes
- **Lotofácil**: Targets 14 and 13 points
- **Mega-Sena**: Targets quadra (4) and quina (5)
- **Best for**: Players seeking more frequent smaller wins

## 📈 Performance Tips

1. **Database**: Keep your database updated for best results
2. **Analysis**: Run full analysis periodically to understand trends
3. **Strategies**: Try different strategies and track results
4. **Diversification**: Generate multiple games with mixed strategies
5. **Budget**: Set a budget and stick to it - use cost calculations

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

Areas for contribution:
- Additional lottery types
- Machine learning models (Random Forest, LSTM)
- Web dashboard (Streamlit/Flask)
- Mobile app integration
- Backtesting framework
- External data source integration

## 📝 License

This project is licensed under the terms specified in the LICENSE file.

## ⚠️ Disclaimer

**IMPORTANT**: This system is for educational and entertainment purposes only. Lottery games are games of chance, and no system can guarantee wins. Play responsibly and within your means.

The statistical analysis and game generation are based on historical data and mathematical principles, but lottery draws are designed to be random and independent events. Past results do not influence future outcomes.

## 🙏 Acknowledgments

- Data sourced from Caixa Econômica Federal
- Built with Python, Pandas, NumPy, SciPy, and SQLAlchemy
- Inspired by the original Lotofácil neural network project

## 📞 Support

For questions, issues, or suggestions:
- Open an issue on GitHub
- Check existing issues for similar problems
- Refer to the documentation in code docstrings

## 🗺️ Roadmap

- [ ] Machine Learning models (Random Forest, LSTM)
- [ ] Web dashboard with visualizations
- [ ] Backtesting framework
- [ ] Automated scheduling for data updates
- [ ] PDF report generation
- [ ] Mobile app
- [ ] Multi-language support
- [ ] Cloud deployment options

---

**Version**: 1.0.0  
**Last Updated**: December 2024  
**Python Version**: 3.11+
