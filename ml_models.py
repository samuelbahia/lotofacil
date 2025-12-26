"""
Machine Learning Models Module for Lottery Analysis System

This module provides machine learning capabilities for predicting
lottery patterns and optimizing game selection.
"""

import logging
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LotteryMLModels:
    """Machine learning models for lottery analysis"""
    
    def __init__(self, config_path: str = './config.yaml'):
        """
        Initialize ML models
        
        Args:
            config_path: Path to configuration file
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.ml_config = self.config.get('machine_learning', {})
        self.models = {}
        self.scalers = {}
    
    def _parse_numbers(self, numbers_str: str) -> List[int]:
        """Parse comma-separated number string to list of integers"""
        return [int(n) for n in numbers_str.split(',')]
    
    def _prepare_features(self, df: pd.DataFrame, lottery_type: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare feature matrix and target from lottery data
        
        Args:
            df: DataFrame with lottery results
            lottery_type: Type of lottery
            
        Returns:
            Tuple of (features, targets)
        """
        total_numbers = self.config['lotteries'][lottery_type]['total_numbers']
        
        # Create binary matrix of number occurrences
        features = []
        for numbers_str in df['numbers']:
            numbers = self._parse_numbers(numbers_str)
            feature_vector = [1 if i in numbers else 0 for i in range(1, total_numbers + 1)]
            features.append(feature_vector)
        
        features = np.array(features)
        
        # Target: next draw's numbers (for training)
        # For now, we'll create a simplified target based on whether numbers appear in next draw
        targets = np.zeros((len(features) - 1, total_numbers))
        for i in range(len(features) - 1):
            targets[i] = features[i + 1]
        
        # Remove last feature row since it has no target
        features = features[:-1]
        
        return features, targets
    
    def train_random_forest(self, df: pd.DataFrame, lottery_type: str) -> Dict:
        """
        Train Random Forest model to predict number occurrences
        
        Args:
            df: DataFrame with lottery results
            lottery_type: Type of lottery
            
        Returns:
            Dictionary with model performance metrics
        """
        if not self.ml_config.get('enabled', False):
            logger.warning("Machine learning is disabled in config")
            return {}
        
        if not self.ml_config['models']['random_forest']['enabled']:
            logger.warning("Random Forest is disabled in config")
            return {}
        
        logger.info(f"Training Random Forest for {lottery_type}")
        
        # Prepare data
        features, targets = self._prepare_features(df, lottery_type)
        
        # Split data
        test_size = self.ml_config['train_test_split']
        X_train, X_test, y_train, y_test = train_test_split(
            features, targets, test_size=test_size, shuffle=False
        )
        
        # Train model for each number position
        rf_config = self.ml_config['models']['random_forest']
        
        # For simplicity, train a single multi-output classifier
        model = RandomForestClassifier(
            n_estimators=rf_config['n_estimators'],
            max_depth=rf_config['max_depth'],
            random_state=42,
            n_jobs=-1
        )
        
        # Convert to single target (sum of occurrences) for demo
        y_train_simple = y_train.sum(axis=1)
        y_test_simple = y_test.sum(axis=1)
        
        model.fit(X_train, y_train_simple)
        
        # Evaluate
        train_score = model.score(X_train, y_train_simple)
        test_score = model.score(X_test, y_test_simple)
        
        # Cross-validation
        cv_scores = cross_val_score(
            model, X_train, y_train_simple,
            cv=min(5, self.ml_config['cross_validation_folds'])
        )
        
        # Store model
        self.models[f'rf_{lottery_type}'] = model
        
        results = {
            'model_type': 'RandomForest',
            'lottery_type': lottery_type,
            'train_score': float(train_score),
            'test_score': float(test_score),
            'cv_mean_score': float(cv_scores.mean()),
            'cv_std_score': float(cv_scores.std()),
            'n_samples_train': len(X_train),
            'n_samples_test': len(X_test)
        }
        
        logger.info(f"Random Forest trained - Test score: {test_score:.3f}")
        
        return results
    
    def predict_number_probabilities(self, df: pd.DataFrame, 
                                     lottery_type: str) -> Dict[int, float]:
        """
        Predict probability of each number appearing in next draw
        
        Args:
            df: DataFrame with lottery results
            lottery_type: Type of lottery
            
        Returns:
            Dictionary mapping number to probability
        """
        model_key = f'rf_{lottery_type}'
        
        if model_key not in self.models:
            logger.warning(f"No trained model found for {lottery_type}")
            # Return uniform probabilities
            total_numbers = self.config['lotteries'][lottery_type]['total_numbers']
            return {i: 1.0/total_numbers for i in range(1, total_numbers + 1)}
        
        # Get latest draw as context
        latest = df.iloc[0]
        numbers = self._parse_numbers(latest['numbers'])
        total_numbers = self.config['lotteries'][lottery_type]['total_numbers']
        
        feature_vector = np.array([[1 if i in numbers else 0 
                                   for i in range(1, total_numbers + 1)]])
        
        # Predict (simplified)
        model = self.models[model_key]
        
        # Feature importance as proxy for probabilities
        importances = model.feature_importances_
        
        # Normalize to probabilities
        total = importances.sum()
        probabilities = {i+1: float(importances[i]/total) 
                        for i in range(total_numbers)}
        
        return probabilities
    
    def cluster_games(self, df: pd.DataFrame, lottery_type: str,
                     n_clusters: int = None) -> Dict:
        """
        Cluster games to identify patterns
        
        Args:
            df: DataFrame with lottery results
            lottery_type: Type of lottery
            n_clusters: Number of clusters (default from config)
            
        Returns:
            Dictionary with clustering results
        """
        if not self.ml_config.get('enabled', False):
            logger.warning("Machine learning is disabled in config")
            return {}
        
        if not self.ml_config['models']['kmeans']['enabled']:
            logger.warning("K-means is disabled in config")
            return {}
        
        if n_clusters is None:
            n_clusters = self.ml_config['models']['kmeans']['n_clusters']
        
        logger.info(f"Clustering games for {lottery_type}")
        
        # Prepare data
        features, _ = self._prepare_features(df, lottery_type)
        
        # Scale features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # Cluster
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(features_scaled)
        
        # Store scaler
        self.scalers[f'kmeans_{lottery_type}'] = scaler
        self.models[f'kmeans_{lottery_type}'] = kmeans
        
        # Analyze clusters
        # Note: features has one less row than df due to target preparation
        df_subset = df.iloc[:-1]  # Match the features length
        cluster_stats = {}
        for i in range(n_clusters):
            cluster_mask = clusters == i
            cluster_games = df_subset[cluster_mask]
            cluster_stats[f'cluster_{i}'] = {
                'size': len(cluster_games),
                'percentage': len(cluster_games) / len(df_subset) * 100,
                'sample_games': cluster_games.head(3)['numbers'].tolist()
            }
        
        results = {
            'n_clusters': n_clusters,
            'cluster_sizes': [int((clusters == i).sum()) for i in range(n_clusters)],
            'inertia': float(kmeans.inertia_),
            'cluster_stats': cluster_stats
        }
        
        logger.info(f"Clustering complete - {n_clusters} clusters identified")
        
        return results
    
    def backtest_strategy(self, df: pd.DataFrame, lottery_type: str,
                         strategy_func, n_draws: int = 100) -> Dict:
        """
        Backtest a game generation strategy
        
        Args:
            df: DataFrame with lottery results (sorted newest first)
            lottery_type: Type of lottery
            strategy_func: Function that generates games
            n_draws: Number of draws to backtest
            
        Returns:
            Dictionary with backtest results
        """
        logger.info(f"Backtesting strategy for {n_draws} draws")
        
        hits = {i: 0 for i in range(26)}  # Count hits per draw
        total_cost = 0
        total_prize = 0
        
        draw_count = self.config['lotteries'][lottery_type]['draw_count']
        
        # Process each draw
        for i in range(min(n_draws, len(df))):
            # Generate games based on data up to this point
            historical_df = df.iloc[i+1:]  # All draws before this one
            
            if len(historical_df) < 10:
                continue
            
            # Generate game using strategy
            try:
                generated_numbers = strategy_func(historical_df, lottery_type)
                actual_numbers = self._parse_numbers(df.iloc[i]['numbers'])
                
                # Count matches
                matches = len(set(generated_numbers) & set(actual_numbers))
                hits[matches] += 1
                
                # Simplified prize calculation
                total_cost += 2.50  # Minimum bet
                
                # Prize for Lotofácil (simplified)
                if lottery_type == 'lotofacil':
                    if matches == 15:
                        total_prize += 1000000  # Simplified
                    elif matches == 14:
                        total_prize += 1000
                    elif matches == 13:
                        total_prize += 25
                    elif matches == 12:
                        total_prize += 10
                    elif matches == 11:
                        total_prize += 5
                        
            except Exception as e:
                logger.warning(f"Error in backtest iteration {i}: {e}")
                continue
        
        # Calculate statistics
        total_games = sum(hits.values())
        roi = ((total_prize - total_cost) / total_cost * 100) if total_cost > 0 else 0
        
        results = {
            'n_draws_tested': total_games,
            'total_cost': total_cost,
            'total_prize': total_prize,
            'roi_percentage': roi,
            'hit_distribution': {k: v for k, v in hits.items() if v > 0},
            'best_result': max(hits.keys()) if hits else 0,
            'average_matches': sum(k*v for k, v in hits.items()) / total_games if total_games > 0 else 0
        }
        
        logger.info(f"Backtest complete - ROI: {roi:.2f}%")
        
        return results


def main():
    """Main function for command-line usage"""
    import argparse
    from data_collector import DataCollector
    import json
    
    parser = argparse.ArgumentParser(description='Lottery ML Models')
    parser.add_argument('--lottery', type=str, required=True,
                       help='Lottery type (lotofacil, megasena, quina)')
    parser.add_argument('--train-rf', action='store_true',
                       help='Train Random Forest model')
    parser.add_argument('--cluster', action='store_true',
                       help='Perform clustering analysis')
    parser.add_argument('--predict', action='store_true',
                       help='Predict number probabilities')
    parser.add_argument('--output', type=str, help='Output file for results (JSON)')
    parser.add_argument('--config', type=str, default='./config.yaml',
                       help='Config file path')
    
    args = parser.parse_args()
    
    # Load data
    collector = DataCollector(config_path=args.config)
    df = collector.get_lottery_data(args.lottery)
    
    if df.empty:
        print(f"No data found for {args.lottery}. Please run data collector first.")
        return
    
    # Initialize ML models
    ml = LotteryMLModels(config_path=args.config)
    
    results = {}
    
    if args.train_rf:
        results['random_forest'] = ml.train_random_forest(df, args.lottery)
        print(f"\nRandom Forest Results:")
        print(f"  Train Score: {results['random_forest']['train_score']:.3f}")
        print(f"  Test Score: {results['random_forest']['test_score']:.3f}")
        print(f"  CV Mean Score: {results['random_forest']['cv_mean_score']:.3f}")
    
    if args.cluster:
        results['clustering'] = ml.cluster_games(df, args.lottery)
        print(f"\nClustering Results:")
        print(f"  Number of Clusters: {results['clustering']['n_clusters']}")
        print(f"  Cluster Sizes: {results['clustering']['cluster_sizes']}")
    
    if args.predict:
        results['predictions'] = ml.predict_number_probabilities(df, args.lottery)
        top_numbers = sorted(results['predictions'].items(), 
                           key=lambda x: x[1], reverse=True)[:10]
        print(f"\nTop 10 Predicted Numbers:")
        for num, prob in top_numbers:
            print(f"  Number {num:2d}: {prob:.4f}")
    
    # Save results
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nResults saved to {args.output}")


if __name__ == '__main__':
    main()
