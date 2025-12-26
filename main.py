#!/usr/bin/env python3
"""
Main CLI Entry Point for Lottery Analysis System

This is the main command-line interface for the lottery analysis system,
providing access to all major functionality.
"""

import argparse
import logging
import sys
import os
from datetime import datetime
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_collector import DataCollector
from statistical_analysis import StatisticalAnalysis
from game_generator import GameGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LotterySystem:
    """Main lottery analysis system coordinator"""
    
    def __init__(self, config_path: str = './config.yaml'):
        """
        Initialize lottery system
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.collector = DataCollector(config_path)
        self.analyzer = StatisticalAnalysis(config_path)
        self.generator = GameGenerator(config_path)
    
    def update_data(self, lottery_type: str = None):
        """Update lottery data from official sources"""
        print("\n" + "="*60)
        print("UPDATING LOTTERY DATA")
        print("="*60 + "\n")
        
        if lottery_type:
            new, existing = self.collector.update_lottery_data(lottery_type)
            print(f"\n{lottery_type.upper()} Updated:")
            print(f"  New records: {new}")
            print(f"  Existing records: {existing}")
        else:
            results = self.collector.update_all_lotteries()
            for lot_type, (new, existing) in results.items():
                print(f"\n{lot_type.upper()}:")
                print(f"  New records: {new}")
                print(f"  Existing records: {existing}")
        
        print("\n" + "="*60 + "\n")
    
    def show_statistics(self, lottery_type: str):
        """Show database statistics"""
        stats = self.collector.get_statistics(lottery_type)
        
        print("\n" + "="*60)
        print(f"{lottery_type.upper()} - DATABASE STATISTICS")
        print("="*60)
        print(f"  Total draws in database: {stats['total_draws']}")
        print(f"  Latest draw number: #{stats['latest_draw_number']}")
        print(f"  Latest draw date: {stats['latest_draw_date']}")
        print("="*60 + "\n")
    
    def analyze(self, lottery_type: str, output_file: str = None):
        """Perform comprehensive statistical analysis"""
        print("\n" + "="*60)
        print(f"{lottery_type.upper()} - STATISTICAL ANALYSIS")
        print("="*60 + "\n")
        
        # Load data
        df = self.collector.get_lottery_data(lottery_type)
        
        if df.empty:
            print(f"No data found for {lottery_type}. Please run --update first.")
            return
        
        # Generate comprehensive report
        report = self.analyzer.generate_comprehensive_report(df, lottery_type)
        
        # Display key findings
        print(f"Total draws analyzed: {report['total_draws']}\n")
        
        print("TOP 10 MOST FREQUENT NUMBERS:")
        for i, freq_data in enumerate(report['frequency'][:10], 1):
            print(f"  {i:2d}. Number {freq_data['number']:2d}: "
                  f"{freq_data['absolute_frequency']:4d} times "
                  f"({freq_data['percentage']:.1f}%)")
        
        print(f"\nHOT NUMBERS (Recent): {report['hot_cold']['hot_numbers']}")
        print(f"COLD NUMBERS (Recent): {report['hot_cold']['cold_numbers']}")
        
        print(f"\nEVEN/ODD DISTRIBUTION:")
        print(f"  Average Even: {report['even_odd']['average_even']:.1f}")
        print(f"  Average Odd: {report['even_odd']['average_odd']:.1f}")
        print(f"  Most Common: {report['even_odd']['most_common'][:3]}")
        
        print(f"\nSUM STATISTICS:")
        print(f"  Mean: {report['sum_stats']['mean']:.1f}")
        print(f"  Median: {report['sum_stats']['median']:.1f}")
        print(f"  Range: {report['sum_stats']['min']:.0f} - {report['sum_stats']['max']:.0f}")
        
        print(f"\nTOP 5 NUMBER PAIRS:")
        for i, (pair, count) in enumerate(report['top_pairs'][:5], 1):
            print(f"  {i}. {pair}: {count} times")
        
        print(f"\nRANDOMNESS TEST (Chi-Square):")
        print(f"  p-value: {report['chi_square']['p_value']:.4f}")
        print(f"  Interpretation: {report['chi_square']['interpretation']}")
        
        print("\n" + "="*60 + "\n")
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"Full report saved to: {output_file}\n")
    
    def generate_games(self, lottery_type: str, count: int = 10,
                      strategy: str = 'all', output_file: str = None):
        """Generate lottery games"""
        print("\n" + "="*60)
        print(f"{lottery_type.upper()} - GAME GENERATION")
        print("="*60 + "\n")
        
        # Determine strategies
        if strategy == 'all':
            strategies = ['conservative', 'balanced', 'aggressive', 'intermediate']
        else:
            strategies = [strategy]
        
        # Generate games
        try:
            games = self.generator.generate_multiple_games(
                lottery_type,
                count=count,
                strategies=strategies
            )
            
            # Display games
            output = self.generator.format_games_output(games, lottery_type)
            print(output)
            
            # Save to file if requested
            if output_file:
                # Save JSON
                json_file = output_file.replace('.txt', '.json')
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(games, f, indent=2)
                
                # Save readable text
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(output)
                
                print(f"\nGames saved to: {output_file}")
                print(f"JSON data saved to: {json_file}\n")
                
        except Exception as e:
            logger.error(f"Error generating games: {e}")
            raise
    
    def quick_play(self, lottery_type: str):
        """Quick play: update, analyze, and generate games"""
        print("\n" + "="*70)
        print("LOTTERY SYSTEM - QUICK PLAY")
        print("="*70 + "\n")
        
        # Update data
        print("Step 1: Updating data...")
        self.update_data(lottery_type)
        
        # Show stats
        print("Step 2: Database statistics...")
        self.show_statistics(lottery_type)
        
        # Quick analysis
        print("Step 3: Analyzing patterns...")
        df = self.collector.get_lottery_data(lottery_type)
        if not df.empty:
            hot_cold = self.analyzer.identify_hot_cold_numbers(df, lottery_type)
            print(f"  Hot numbers: {hot_cold['hot_numbers'][:5]}")
            print(f"  Cold numbers: {hot_cold['cold_numbers'][:5]}\n")
        
        # Generate games
        print("Step 4: Generating games...")
        self.generate_games(lottery_type, count=6, strategy='all')
        
        print("="*70 + "\n")


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description='Lottery Analysis System - Complete solution for lottery analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update all lottery data
  python main.py --update
  
  # Update specific lottery
  python main.py --update --lottery lotofacil
  
  # Analyze lottery patterns
  python main.py --analyze --lottery lotofacil
  
  # Generate games
  python main.py --generate-games --lottery megasena --count 10
  
  # Quick play (update, analyze, generate)
  python main.py --quick-play --lottery quina
  
  # Show statistics
  python main.py --stats --lottery lotofacil
        """
    )
    
    # Main actions
    parser.add_argument('--update', action='store_true',
                       help='Update lottery data from official sources')
    parser.add_argument('--analyze', action='store_true',
                       help='Perform statistical analysis')
    parser.add_argument('--generate-games', action='store_true',
                       help='Generate lottery games')
    parser.add_argument('--stats', action='store_true',
                       help='Show database statistics')
    parser.add_argument('--quick-play', action='store_true',
                       help='Quick play: update, analyze, and generate games')
    
    # Options
    parser.add_argument('--lottery', type=str,
                       choices=['lotofacil', 'megasena', 'quina', 'lotomania'],
                       help='Lottery type to process')
    parser.add_argument('--count', type=int, default=10,
                       help='Number of games to generate (default: 10)')
    parser.add_argument('--strategy', type=str,
                       choices=['conservative', 'aggressive', 'balanced', 'intermediate', 'all'],
                       default='all',
                       help='Game generation strategy (default: all)')
    parser.add_argument('--output', type=str,
                       help='Output file for results')
    parser.add_argument('--config', type=str, default='./config.yaml',
                       help='Configuration file path (default: ./config.yaml)')
    
    args = parser.parse_args()
    
    # Show help if no arguments
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    
    try:
        # Initialize system
        system = LotterySystem(config_path=args.config)
        
        # Execute requested action
        if args.update:
            system.update_data(args.lottery)
        
        if args.stats:
            if not args.lottery:
                print("Error: --stats requires --lottery parameter")
                sys.exit(1)
            system.show_statistics(args.lottery)
        
        if args.analyze:
            if not args.lottery:
                print("Error: --analyze requires --lottery parameter")
                sys.exit(1)
            system.analyze(args.lottery, args.output)
        
        if args.generate_games:
            if not args.lottery:
                print("Error: --generate-games requires --lottery parameter")
                sys.exit(1)
            system.generate_games(
                args.lottery,
                count=args.count,
                strategy=args.strategy,
                output_file=args.output
            )
        
        if args.quick_play:
            if not args.lottery:
                print("Error: --quick-play requires --lottery parameter")
                sys.exit(1)
            system.quick_play(args.lottery)
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
