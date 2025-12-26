"""
Statistical Analysis Module for Lottery Analysis System

This module provides comprehensive statistical analysis of lottery data including
frequency analysis, pattern detection, correlation analysis, and temporal trends.
"""

import logging
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from scipy import stats
from collections import Counter, defaultdict
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StatisticalAnalysis:
    """Main class for statistical analysis of lottery data"""
    
    def __init__(self, config_path: str = './config.yaml'):
        """
        Initialize statistical analysis
        
        Args:
            config_path: Path to configuration file
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.analysis_config = self.config['analysis']
    
    def _parse_numbers(self, numbers_str: str) -> List[int]:
        """Parse comma-separated number string to list of integers"""
        return [int(n) for n in numbers_str.split(',')]
    
    def calculate_frequency(self, df: pd.DataFrame, lottery_type: str) -> pd.DataFrame:
        """
        Calculate absolute and relative frequency of each number
        
        Args:
            df: DataFrame with lottery results
            lottery_type: Type of lottery
            
        Returns:
            DataFrame with frequency statistics
        """
        total_numbers = self.config['lotteries'][lottery_type]['total_numbers']
        
        # Count occurrences of each number
        number_counts = Counter()
        total_draws = len(df)
        
        for numbers_str in df['numbers']:
            numbers = self._parse_numbers(numbers_str)
            number_counts.update(numbers)
        
        # Create frequency DataFrame
        freq_data = []
        for number in range(1, total_numbers + 1):
            count = number_counts.get(number, 0)
            freq_data.append({
                'number': number,
                'absolute_frequency': count,
                'relative_frequency': count / total_draws if total_draws > 0 else 0,
                'percentage': (count / total_draws * 100) if total_draws > 0 else 0
            })
        
        freq_df = pd.DataFrame(freq_data)
        freq_df = freq_df.sort_values('absolute_frequency', ascending=False)
        
        return freq_df
    
    def calculate_recent_frequency(self, df: pd.DataFrame, lottery_type: str, 
                                   last_n: int = 50) -> pd.DataFrame:
        """
        Calculate frequency for recent draws
        
        Args:
            df: DataFrame with lottery results (sorted by draw_number desc)
            lottery_type: Type of lottery
            last_n: Number of recent draws to analyze
            
        Returns:
            DataFrame with recent frequency statistics
        """
        recent_df = df.head(last_n)
        return self.calculate_frequency(recent_df, lottery_type)
    
    def identify_hot_cold_numbers(self, df: pd.DataFrame, lottery_type: str,
                                  last_n: int = 100) -> Dict:
        """
        Identify hot (frequent) and cold (infrequent) numbers
        
        Args:
            df: DataFrame with lottery results
            lottery_type: Type of lottery
            last_n: Number of recent draws to analyze
            
        Returns:
            Dictionary with hot and cold numbers
        """
        freq_df = self.calculate_recent_frequency(df, lottery_type, last_n)
        
        # Calculate median frequency
        median_freq = freq_df['absolute_frequency'].median()
        
        hot_numbers = freq_df[freq_df['absolute_frequency'] > median_freq]['number'].tolist()
        cold_numbers = freq_df[freq_df['absolute_frequency'] < median_freq]['number'].tolist()
        
        return {
            'hot_numbers': hot_numbers[:10],  # Top 10 hot numbers
            'cold_numbers': cold_numbers[-10:],  # Bottom 10 cold numbers
            'median_frequency': median_freq
        }
    
    def calculate_moving_average(self, df: pd.DataFrame, lottery_type: str,
                                window: int = 10) -> pd.DataFrame:
        """
        Calculate moving average of number appearances
        
        Args:
            df: DataFrame with lottery results
            lottery_type: Type of lottery
            window: Window size for moving average
            
        Returns:
            DataFrame with moving averages
        """
        total_numbers = self.config['lotteries'][lottery_type]['total_numbers']
        
        # Create matrix of number appearances per draw
        draws = []
        for numbers_str in df['numbers']:
            numbers = self._parse_numbers(numbers_str)
            draw_vector = [1 if i in numbers else 0 for i in range(1, total_numbers + 1)]
            draws.append(draw_vector)
        
        draws_matrix = np.array(draws)
        
        # Calculate moving average for each number
        ma_data = []
        for i in range(total_numbers):
            number = i + 1
            appearances = draws_matrix[:, i]
            
            # Calculate moving average
            if len(appearances) >= window:
                ma = np.convolve(appearances, np.ones(window)/window, mode='valid')
                current_ma = ma[-1] if len(ma) > 0 else 0
            else:
                current_ma = np.mean(appearances)
            
            ma_data.append({
                'number': number,
                'moving_average': current_ma,
                'trend': 'up' if current_ma > np.mean(appearances) else 'down'
            })
        
        return pd.DataFrame(ma_data)
    
    def analyze_cycles(self, df: pd.DataFrame, lottery_type: str) -> pd.DataFrame:
        """
        Analyze cycles (time between appearances) for each number
        
        Args:
            df: DataFrame with lottery results
            lottery_type: Type of lottery
            
        Returns:
            DataFrame with cycle statistics
        """
        total_numbers = self.config['lotteries'][lottery_type]['total_numbers']
        
        cycle_data = []
        
        for number in range(1, total_numbers + 1):
            appearances = []
            
            for idx, numbers_str in enumerate(df['numbers']):
                numbers = self._parse_numbers(numbers_str)
                if number in numbers:
                    appearances.append(idx)
            
            if len(appearances) > 1:
                cycles = [appearances[i+1] - appearances[i] for i in range(len(appearances)-1)]
                avg_cycle = np.mean(cycles)
                std_cycle = np.std(cycles)
                min_cycle = np.min(cycles)
                max_cycle = np.max(cycles)
                
                # Calculate how long since last appearance
                last_appearance = appearances[-1] if appearances else len(df)
                draws_since_last = last_appearance
            else:
                avg_cycle = std_cycle = min_cycle = max_cycle = 0
                draws_since_last = len(df)
            
            cycle_data.append({
                'number': number,
                'avg_cycle': avg_cycle,
                'std_cycle': std_cycle,
                'min_cycle': min_cycle,
                'max_cycle': max_cycle,
                'draws_since_last': draws_since_last,
                'total_appearances': len(appearances)
            })
        
        return pd.DataFrame(cycle_data)
    
    def analyze_even_odd_distribution(self, df: pd.DataFrame) -> Dict:
        """
        Analyze even/odd distribution patterns
        
        Args:
            df: DataFrame with lottery results
            
        Returns:
            Dictionary with even/odd statistics
        """
        distributions = []
        
        for numbers_str in df['numbers']:
            numbers = self._parse_numbers(numbers_str)
            even_count = sum(1 for n in numbers if n % 2 == 0)
            odd_count = len(numbers) - even_count
            distributions.append((even_count, odd_count))
        
        distribution_counts = Counter(distributions)
        most_common = distribution_counts.most_common(5)
        
        return {
            'distributions': distribution_counts,
            'most_common': most_common,
            'average_even': np.mean([d[0] for d in distributions]),
            'average_odd': np.mean([d[1] for d in distributions])
        }
    
    def analyze_prime_distribution(self, df: pd.DataFrame) -> Dict:
        """
        Analyze prime/non-prime distribution patterns
        
        Args:
            df: DataFrame with lottery results
            
        Returns:
            Dictionary with prime statistics
        """
        def is_prime(n):
            if n < 2:
                return False
            for i in range(2, int(n**0.5) + 1):
                if n % i == 0:
                    return False
            return True
        
        distributions = []
        
        for numbers_str in df['numbers']:
            numbers = self._parse_numbers(numbers_str)
            prime_count = sum(1 for n in numbers if is_prime(n))
            non_prime_count = len(numbers) - prime_count
            distributions.append((prime_count, non_prime_count))
        
        distribution_counts = Counter(distributions)
        most_common = distribution_counts.most_common(5)
        
        return {
            'distributions': distribution_counts,
            'most_common': most_common,
            'average_prime': np.mean([d[0] for d in distributions]),
            'average_non_prime': np.mean([d[1] for d in distributions])
        }
    
    def detect_sequences(self, df: pd.DataFrame, min_length: int = 2) -> Dict:
        """
        Detect consecutive number sequences
        
        Args:
            df: DataFrame with lottery results
            min_length: Minimum sequence length to detect
            
        Returns:
            Dictionary with sequence statistics
        """
        sequence_counts = Counter()
        
        for numbers_str in df['numbers']:
            numbers = sorted(self._parse_numbers(numbers_str))
            
            # Find consecutive sequences
            sequences = []
            current_seq = [numbers[0]]
            
            for i in range(1, len(numbers)):
                if numbers[i] == current_seq[-1] + 1:
                    current_seq.append(numbers[i])
                else:
                    if len(current_seq) >= min_length:
                        sequences.append(tuple(current_seq))
                    current_seq = [numbers[i]]
            
            if len(current_seq) >= min_length:
                sequences.append(tuple(current_seq))
            
            for seq in sequences:
                sequence_counts[len(seq)] += 1
        
        return {
            'sequence_length_counts': dict(sequence_counts),
            'total_sequences': sum(sequence_counts.values()),
            'percentage_with_sequences': (sum(1 for s in df['numbers'] 
                                             if self._has_sequence(s, min_length)) / len(df) * 100)
        }
    
    def _has_sequence(self, numbers_str: str, min_length: int) -> bool:
        """Check if numbers contain a sequence of minimum length"""
        numbers = sorted(self._parse_numbers(numbers_str))
        current_length = 1
        
        for i in range(1, len(numbers)):
            if numbers[i] == numbers[i-1] + 1:
                current_length += 1
                if current_length >= min_length:
                    return True
            else:
                current_length = 1
        
        return False
    
    def analyze_sum_distribution(self, df: pd.DataFrame) -> Dict:
        """
        Analyze distribution of sum of drawn numbers
        
        Args:
            df: DataFrame with lottery results
            
        Returns:
            Dictionary with sum statistics
        """
        sums = []
        
        for numbers_str in df['numbers']:
            numbers = self._parse_numbers(numbers_str)
            sums.append(sum(numbers))
        
        return {
            'mean': np.mean(sums),
            'median': np.median(sums),
            'std': np.std(sums),
            'min': np.min(sums),
            'max': np.max(sums),
            'percentile_25': np.percentile(sums, 25),
            'percentile_75': np.percentile(sums, 75)
        }
    
    def analyze_correlation(self, df: pd.DataFrame, lottery_type: str) -> pd.DataFrame:
        """
        Analyze correlation between numbers (co-occurrence)
        
        Args:
            df: DataFrame with lottery results
            lottery_type: Type of lottery
            
        Returns:
            DataFrame with correlation matrix
        """
        total_numbers = self.config['lotteries'][lottery_type]['total_numbers']
        
        # Create co-occurrence matrix
        cooccurrence = np.zeros((total_numbers, total_numbers))
        
        for numbers_str in df['numbers']:
            numbers = self._parse_numbers(numbers_str)
            for i in numbers:
                for j in numbers:
                    if i != j:
                        cooccurrence[i-1][j-1] += 1
        
        # Convert to correlation (normalize by frequency)
        correlation_matrix = pd.DataFrame(
            cooccurrence,
            index=range(1, total_numbers + 1),
            columns=range(1, total_numbers + 1)
        )
        
        return correlation_matrix
    
    def find_frequent_pairs(self, df: pd.DataFrame, top_n: int = 10) -> List[Tuple]:
        """
        Find most frequent number pairs
        
        Args:
            df: DataFrame with lottery results
            top_n: Number of top pairs to return
            
        Returns:
            List of (pair, count) tuples
        """
        pair_counts = Counter()
        
        for numbers_str in df['numbers']:
            numbers = self._parse_numbers(numbers_str)
            
            # Generate all pairs
            for i in range(len(numbers)):
                for j in range(i+1, len(numbers)):
                    pair = tuple(sorted([numbers[i], numbers[j]]))
                    pair_counts[pair] += 1
        
        return pair_counts.most_common(top_n)
    
    def find_frequent_triplets(self, df: pd.DataFrame, top_n: int = 10) -> List[Tuple]:
        """
        Find most frequent number triplets
        
        Args:
            df: DataFrame with lottery results
            top_n: Number of top triplets to return
            
        Returns:
            List of (triplet, count) tuples
        """
        triplet_counts = Counter()
        
        for numbers_str in df['numbers']:
            numbers = self._parse_numbers(numbers_str)
            
            # Generate all triplets
            for i in range(len(numbers)):
                for j in range(i+1, len(numbers)):
                    for k in range(j+1, len(numbers)):
                        triplet = tuple(sorted([numbers[i], numbers[j], numbers[k]]))
                        triplet_counts[triplet] += 1
        
        return triplet_counts.most_common(top_n)
    
    def chi_square_test(self, df: pd.DataFrame, lottery_type: str) -> Dict:
        """
        Perform chi-square test for randomness
        
        Args:
            df: DataFrame with lottery results
            lottery_type: Type of lottery
            
        Returns:
            Dictionary with test results
        """
        freq_df = self.calculate_frequency(df, lottery_type)
        
        observed = freq_df['absolute_frequency'].values
        expected = np.full(len(observed), observed.mean())
        
        chi2, p_value = stats.chisquare(observed, expected)
        
        return {
            'chi_square': chi2,
            'p_value': p_value,
            'is_random': p_value > 0.05,  # 95% confidence level
            'interpretation': 'Distribution appears random' if p_value > 0.05 
                            else 'Distribution shows non-random patterns'
        }
    
    def analyze_quadrants(self, df: pd.DataFrame, lottery_type: str) -> Dict:
        """
        Analyze distribution across quadrants of the lottery card
        
        Args:
            df: DataFrame with lottery results
            lottery_type: Type of lottery
            
        Returns:
            Dictionary with quadrant statistics
        """
        total_numbers = self.config['lotteries'][lottery_type]['total_numbers']
        
        # Determine quadrant size (assumes square-ish layout)
        # For Lotofácil (25 numbers): 5x5 grid
        # For Mega-Sena (60 numbers): treat as 8x8 approx
        if total_numbers == 25:
            grid_size = 5
        elif total_numbers == 60:
            grid_size = 8
        else:
            grid_size = int(np.sqrt(total_numbers))
        
        half = grid_size // 2
        
        quadrant_counts = {
            'Q1': 0,  # Top-left
            'Q2': 0,  # Top-right
            'Q3': 0,  # Bottom-left
            'Q4': 0   # Bottom-right
        }
        
        for numbers_str in df['numbers']:
            numbers = self._parse_numbers(numbers_str)
            
            for num in numbers:
                # Calculate position in grid (0-indexed)
                row = (num - 1) // grid_size
                col = (num - 1) % grid_size
                
                if row < half and col < half:
                    quadrant_counts['Q1'] += 1
                elif row < half and col >= half:
                    quadrant_counts['Q2'] += 1
                elif row >= half and col < half:
                    quadrant_counts['Q3'] += 1
                else:
                    quadrant_counts['Q4'] += 1
        
        total = sum(quadrant_counts.values())
        quadrant_percentages = {k: (v/total*100) if total > 0 else 0 
                               for k, v in quadrant_counts.items()}
        
        return {
            'counts': quadrant_counts,
            'percentages': quadrant_percentages,
            'most_common_quadrant': max(quadrant_counts, key=quadrant_counts.get)
        }
    
    def generate_comprehensive_report(self, df: pd.DataFrame, 
                                     lottery_type: str) -> Dict:
        """
        Generate comprehensive statistical report
        
        Args:
            df: DataFrame with lottery results
            lottery_type: Type of lottery
            
        Returns:
            Dictionary with all statistical analyses
        """
        logger.info(f"Generating comprehensive report for {lottery_type}")
        
        report = {
            'lottery_type': lottery_type,
            'total_draws': len(df),
            'frequency': self.calculate_frequency(df, lottery_type).to_dict('records'),
            'hot_cold': self.identify_hot_cold_numbers(df, lottery_type),
            'cycles': self.analyze_cycles(df, lottery_type).to_dict('records'),
            'even_odd': self.analyze_even_odd_distribution(df),
            'prime': self.analyze_prime_distribution(df),
            'sequences': self.detect_sequences(df),
            'sum_stats': self.analyze_sum_distribution(df),
            'top_pairs': self.find_frequent_pairs(df),
            'top_triplets': self.find_frequent_triplets(df),
            'chi_square': self.chi_square_test(df, lottery_type),
            'quadrants': self.analyze_quadrants(df, lottery_type)
        }
        
        return report


def main():
    """Main function for command-line usage"""
    import argparse
    from data_collector import DataCollector
    import json
    
    parser = argparse.ArgumentParser(description='Lottery Statistical Analysis')
    parser.add_argument('--lottery', type=str, required=True, 
                       help='Lottery type (lotofacil, megasena, quina)')
    parser.add_argument('--report', action='store_true', 
                       help='Generate comprehensive report')
    parser.add_argument('--output', type=str, help='Output file for report (JSON)')
    parser.add_argument('--config', type=str, default='./config.yaml', 
                       help='Config file path')
    
    args = parser.parse_args()
    
    # Load data
    collector = DataCollector(config_path=args.config)
    df = collector.get_lottery_data(args.lottery)
    
    if df.empty:
        print(f"No data found for {args.lottery}. Please run data collector first.")
        return
    
    # Perform analysis
    analyzer = StatisticalAnalysis(config_path=args.config)
    
    if args.report:
        report = analyzer.generate_comprehensive_report(df, args.lottery)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"Report saved to {args.output}")
        else:
            print(json.dumps(report, indent=2, default=str))
    else:
        # Show basic statistics
        freq = analyzer.calculate_frequency(df, args.lottery)
        hot_cold = analyzer.identify_hot_cold_numbers(df, args.lottery)
        
        print(f"\n{args.lottery.upper()} Statistics:")
        print(f"Total draws: {len(df)}")
        print(f"\nTop 10 Most Frequent Numbers:")
        print(freq.head(10).to_string(index=False))
        print(f"\nHot Numbers: {hot_cold['hot_numbers']}")
        print(f"Cold Numbers: {hot_cold['cold_numbers']}")


if __name__ == '__main__':
    main()
