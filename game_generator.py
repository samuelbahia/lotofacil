"""
Game Generator Module for Lottery Analysis System

This module generates intelligent lottery games based on statistical analysis
and multiple strategies.
"""

import logging
from typing import Dict, List, Tuple, Optional, Set
import random
import numpy as np
import pandas as pd
import yaml
from itertools import combinations
from statistical_analysis import StatisticalAnalysis
from data_collector import DataCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GameGenerator:
    """Main class for generating lottery games"""
    
    def __init__(self, config_path: str = './config.yaml'):
        """
        Initialize game generator
        
        Args:
            config_path: Path to configuration file
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.analyzer = StatisticalAnalysis(config_path)
        self.collector = DataCollector(config_path)
    
    def _calculate_number_weights(self, df: pd.DataFrame, lottery_type: str,
                                  strategy: str) -> Dict[int, float]:
        """
        Calculate weights for each number based on strategy
        
        Args:
            df: DataFrame with lottery results
            lottery_type: Type of lottery
            strategy: Strategy name (conservative, aggressive, balanced)
            
        Returns:
            Dictionary mapping number to weight
        """
        total_numbers = self.config['lotteries'][lottery_type]['total_numbers']
        strategy_config = self.config['strategies'][strategy]
        
        # Get frequency analysis
        freq_df = self.analyzer.calculate_frequency(df, lottery_type)
        hot_cold = self.analyzer.identify_hot_cold_numbers(df, lottery_type, last_n=100)
        cycles = self.analyzer.analyze_cycles(df, lottery_type)
        
        weights = {}
        
        for number in range(1, total_numbers + 1):
            weight = 0.0
            
            # Frequency component
            freq_row = freq_df[freq_df['number'] == number]
            if not freq_row.empty:
                rel_freq = freq_row['relative_frequency'].values[0]
                weight += strategy_config['weight_frequency'] * rel_freq
            
            # Hot/Cold component
            if number in hot_cold['hot_numbers']:
                weight += strategy_config['weight_hot_numbers']
            elif number in hot_cold['cold_numbers']:
                weight += strategy_config['weight_cold_numbers']
            
            # Cycle component (numbers due to appear)
            cycle_row = cycles[cycles['number'] == number]
            if not cycle_row.empty:
                avg_cycle = cycle_row['avg_cycle'].values[0]
                draws_since = cycle_row['draws_since_last'].values[0]
                if avg_cycle > 0:
                    cycle_factor = min(draws_since / avg_cycle, 2.0)  # Cap at 2x
                    weight += 0.1 * cycle_factor
            
            weights[number] = max(weight, 0.01)  # Ensure minimum weight
        
        # Normalize weights
        total_weight = sum(weights.values())
        weights = {k: v/total_weight for k, v in weights.items()}
        
        return weights
    
    def _select_numbers_weighted(self, weights: Dict[int, float], 
                                 count: int) -> List[int]:
        """
        Select numbers using weighted random selection
        
        Args:
            weights: Dictionary of number weights
            count: How many numbers to select
            
        Returns:
            List of selected numbers
        """
        numbers = list(weights.keys())
        probabilities = [weights[n] for n in numbers]
        
        selected = np.random.choice(
            numbers, 
            size=count, 
            replace=False, 
            p=probabilities
        )
        
        return sorted(selected.tolist())
    
    def _is_valid_game(self, numbers: List[int], lottery_type: str, 
                      strategy: str) -> bool:
        """
        Validate if game meets strategy criteria
        
        Args:
            numbers: List of numbers in game
            lottery_type: Type of lottery
            strategy: Strategy name
            
        Returns:
            True if valid, False otherwise
        """
        strategy_config = self.config['strategies'][strategy]
        generation_config = self.config['game_generation']
        
        # Check for all sequential numbers
        if generation_config['avoid_obvious_patterns']:
            sorted_nums = sorted(numbers)
            is_sequential = all(sorted_nums[i+1] - sorted_nums[i] == 1 
                              for i in range(len(sorted_nums)-1))
            if is_sequential:
                return False
            
            # Check for all multiples of same number
            for base in range(2, 6):
                if all(n % base == 0 for n in numbers):
                    return False
        
        # Check even/odd balance for conservative/balanced strategies
        if strategy in ['conservative', 'balanced']:
            if strategy_config.get('ensure_even_odd_balance', False):
                even_count = sum(1 for n in numbers if n % 2 == 0)
                odd_count = len(numbers) - even_count
                
                # Require some balance (not all even or all odd)
                if even_count == 0 or odd_count == 0:
                    return False
                
                # For balanced, prefer closer to 50/50
                if strategy == 'balanced':
                    ratio = min(even_count, odd_count) / max(even_count, odd_count)
                    if ratio < 0.3:  # Too imbalanced
                        return False
        
        # Check quadrant distribution for balanced strategy
        if strategy == 'balanced' and strategy_config.get('distribute_quadrants', False):
            # Simple quadrant check for Lotofácil (25 numbers)
            if lottery_type == 'lotofacil':
                q1 = sum(1 for n in numbers if n <= 12)  # First half
                q2 = sum(1 for n in numbers if n > 12)   # Second half
                
                # Require some distribution
                if q1 == 0 or q2 == 0:
                    return False
        
        # Check sum range for balanced strategy
        if strategy == 'balanced' and strategy_config.get('target_average_sum', False):
            # Expected sum based on lottery type
            total_nums = self.config['lotteries'][lottery_type]['total_numbers']
            draw_count = self.config['lotteries'][lottery_type]['draw_count']
            
            expected_sum = (total_nums + 1) * draw_count / 2
            actual_sum = sum(numbers)
            
            # Allow 30% deviation from expected
            if abs(actual_sum - expected_sum) > expected_sum * 0.3:
                return False
        
        return True
    
    def generate_conservative_game(self, df: pd.DataFrame, 
                                   lottery_type: str) -> List[int]:
        """
        Generate game using conservative strategy
        
        Args:
            df: DataFrame with lottery results
            lottery_type: Type of lottery
            
        Returns:
            List of selected numbers
        """
        draw_count = self.config['lotteries'][lottery_type]['draw_count']
        weights = self._calculate_number_weights(df, lottery_type, 'conservative')
        
        max_attempts = 1000
        for _ in range(max_attempts):
            numbers = self._select_numbers_weighted(weights, draw_count)
            if self._is_valid_game(numbers, lottery_type, 'conservative'):
                return numbers
        
        # Fallback: return best attempt
        return self._select_numbers_weighted(weights, draw_count)
    
    def generate_aggressive_game(self, df: pd.DataFrame, 
                                lottery_type: str) -> List[int]:
        """
        Generate game using aggressive strategy
        
        Args:
            df: DataFrame with lottery results
            lottery_type: Type of lottery
            
        Returns:
            List of selected numbers
        """
        draw_count = self.config['lotteries'][lottery_type]['draw_count']
        weights = self._calculate_number_weights(df, lottery_type, 'aggressive')
        
        max_attempts = 1000
        for _ in range(max_attempts):
            numbers = self._select_numbers_weighted(weights, draw_count)
            if self._is_valid_game(numbers, lottery_type, 'aggressive'):
                return numbers
        
        return self._select_numbers_weighted(weights, draw_count)
    
    def generate_balanced_game(self, df: pd.DataFrame, 
                              lottery_type: str) -> List[int]:
        """
        Generate game using balanced strategy
        
        Args:
            df: DataFrame with lottery results
            lottery_type: Type of lottery
            
        Returns:
            List of selected numbers
        """
        draw_count = self.config['lotteries'][lottery_type]['draw_count']
        weights = self._calculate_number_weights(df, lottery_type, 'balanced')
        
        max_attempts = 1000
        for _ in range(max_attempts):
            numbers = self._select_numbers_weighted(weights, draw_count)
            if self._is_valid_game(numbers, lottery_type, 'balanced'):
                return numbers
        
        return self._select_numbers_weighted(weights, draw_count)
    
    def generate_intermediate_focused_game(self, df: pd.DataFrame,
                                          lottery_type: str) -> List[int]:
        """
        Generate game focused on intermediate prizes
        
        Args:
            df: DataFrame with lottery results
            lottery_type: Type of lottery
            
        Returns:
            List of selected numbers
        """
        # For Lotofácil, focus on 14-point prizes
        if lottery_type == 'lotofacil':
            # Get most common 14-number combinations from winners
            freq_df = self.analyzer.calculate_frequency(df, lottery_type)
            
            # Select top frequent numbers
            top_numbers = freq_df.head(20)['number'].tolist()
            
            # Randomly select 15 from top 20
            return sorted(random.sample(top_numbers, 15))
        
        # For Mega-Sena, focus on quadra/quina
        elif lottery_type == 'megasena':
            freq_df = self.analyzer.calculate_frequency(df, lottery_type)
            top_numbers = freq_df.head(15)['number'].tolist()
            return sorted(random.sample(top_numbers, 6))
        
        # Default to balanced strategy
        return self.generate_balanced_game(df, lottery_type)
    
    def generate_multiple_games(self, lottery_type: str, 
                               count: int = 10,
                               strategies: Optional[List[str]] = None) -> List[Dict]:
        """
        Generate multiple games with diversification
        
        Args:
            lottery_type: Type of lottery
            count: Number of games to generate
            strategies: List of strategies to use (distributes evenly)
            
        Returns:
            List of game dictionaries with numbers and metadata
        """
        if strategies is None:
            strategies = ['conservative', 'balanced', 'aggressive']
        
        # Load data
        df = self.collector.get_lottery_data(lottery_type)
        if df.empty:
            raise ValueError(f"No data available for {lottery_type}")
        
        games = []
        generated_games: Set[Tuple] = set()
        
        max_overlap = self.config['game_generation']['max_repeated_numbers_across_games']
        draw_count = self.config['lotteries'][lottery_type]['draw_count']
        max_repeated = int(draw_count * max_overlap)
        
        strategies_cycle = strategies * (count // len(strategies) + 1)
        
        for i in range(count):
            strategy = strategies_cycle[i]
            max_attempts = 100
            
            for attempt in range(max_attempts):
                # Generate game based on strategy
                if strategy == 'conservative':
                    numbers = self.generate_conservative_game(df, lottery_type)
                elif strategy == 'aggressive':
                    numbers = self.generate_aggressive_game(df, lottery_type)
                elif strategy == 'balanced':
                    numbers = self.generate_balanced_game(df, lottery_type)
                elif strategy == 'intermediate':
                    numbers = self.generate_intermediate_focused_game(df, lottery_type)
                else:
                    numbers = self.generate_balanced_game(df, lottery_type)
                
                numbers_tuple = tuple(numbers)
                
                # Check if already generated
                if numbers_tuple in generated_games:
                    continue
                
                # Check overlap with existing games
                is_valid = True
                for existing_game in games:
                    existing_numbers = set(existing_game['numbers'])
                    overlap = len(set(numbers) & existing_numbers)
                    
                    if overlap > max_repeated:
                        is_valid = False
                        break
                
                if is_valid:
                    generated_games.add(numbers_tuple)
                    
                    game = {
                        'game_id': i + 1,
                        'strategy': strategy,
                        'numbers': numbers,
                        'cost': self._calculate_cost(lottery_type, len(numbers))
                    }
                    games.append(game)
                    break
            
            if len(games) <= i:
                # Fallback: add game anyway if we couldn't find unique one
                numbers = self.generate_balanced_game(df, lottery_type)
                game = {
                    'game_id': i + 1,
                    'strategy': strategy,
                    'numbers': numbers,
                    'cost': self._calculate_cost(lottery_type, len(numbers))
                }
                games.append(game)
        
        return games
    
    def _calculate_cost(self, lottery_type: str, number_count: int) -> float:
        """
        Calculate cost of a game
        
        Args:
            lottery_type: Type of lottery
            number_count: Number of numbers in game
            
        Returns:
            Cost in currency
        """
        # Simplified cost calculation
        # In reality, this would use official pricing tables
        
        if lottery_type == 'lotofacil':
            costs = {15: 2.50, 16: 40.00, 17: 340.00, 18: 2040.00}
            return costs.get(number_count, 2.50)
        elif lottery_type == 'megasena':
            costs = {6: 5.00, 7: 35.00, 8: 140.00, 9: 420.00, 10: 1050.00}
            return costs.get(number_count, 5.00)
        elif lottery_type == 'quina':
            costs = {5: 2.00, 6: 12.00, 7: 42.00, 8: 112.00}
            return costs.get(number_count, 2.00)
        
        return 2.00  # Default
    
    def calculate_total_investment(self, games: List[Dict]) -> Dict:
        """
        Calculate total investment for a set of games
        
        Args:
            games: List of game dictionaries
            
        Returns:
            Dictionary with investment statistics
        """
        total_cost = sum(game['cost'] for game in games)
        
        strategy_counts = {}
        for game in games:
            strategy = game['strategy']
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        return {
            'total_games': len(games),
            'total_cost': total_cost,
            'average_cost_per_game': total_cost / len(games) if games else 0,
            'strategy_distribution': strategy_counts
        }
    
    def format_games_output(self, games: List[Dict], lottery_type: str) -> str:
        """
        Format games for display
        
        Args:
            games: List of game dictionaries
            lottery_type: Type of lottery
            
        Returns:
            Formatted string
        """
        output = [f"\n{'='*60}"]
        output.append(f"{lottery_type.upper()} - Generated Games")
        output.append(f"{'='*60}\n")
        
        for game in games:
            numbers_str = ' '.join(str(n).zfill(2) for n in game['numbers'])
            output.append(f"Game #{game['game_id']:02d} [{game['strategy'].upper():12s}] "
                         f"R$ {game['cost']:7.2f}")
            output.append(f"  Numbers: {numbers_str}\n")
        
        investment = self.calculate_total_investment(games)
        output.append(f"{'='*60}")
        output.append(f"Total Games: {investment['total_games']}")
        output.append(f"Total Investment: R$ {investment['total_cost']:.2f}")
        output.append(f"Strategy Distribution: {investment['strategy_distribution']}")
        output.append(f"{'='*60}\n")
        
        return '\n'.join(output)


def main():
    """Main function for command-line usage"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Lottery Game Generator')
    parser.add_argument('--lottery', type=str, required=True,
                       help='Lottery type (lotofacil, megasena, quina)')
    parser.add_argument('--count', type=int, default=10,
                       help='Number of games to generate')
    parser.add_argument('--strategy', type=str, 
                       choices=['conservative', 'aggressive', 'balanced', 'intermediate', 'all'],
                       default='all',
                       help='Strategy to use')
    parser.add_argument('--output', type=str, help='Output file for games (JSON)')
    parser.add_argument('--config', type=str, default='./config.yaml',
                       help='Config file path')
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = GameGenerator(config_path=args.config)
    
    # Determine strategies
    if args.strategy == 'all':
        strategies = ['conservative', 'balanced', 'aggressive', 'intermediate']
    else:
        strategies = [args.strategy]
    
    # Generate games
    try:
        games = generator.generate_multiple_games(
            args.lottery,
            count=args.count,
            strategies=strategies
        )
        
        # Display games
        print(generator.format_games_output(games, args.lottery))
        
        # Save to file if requested
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(games, f, indent=2)
            print(f"Games saved to {args.output}")
            
    except Exception as e:
        logger.error(f"Error generating games: {e}")
        raise


if __name__ == '__main__':
    main()
