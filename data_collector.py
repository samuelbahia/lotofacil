"""
Data Collection Module for Lottery Analysis System

This module handles downloading, validating, and storing lottery results
from official sources.
"""

import os
import logging
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
import requests
from sqlalchemy import create_engine, Column, Integer, String, Date, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import yaml
import ssl

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

Base = declarative_base()


class LotteryResult(Base):
    """Database model for lottery results"""
    __tablename__ = 'lottery_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    lottery_type = Column(String(50), nullable=False, index=True)
    draw_number = Column(Integer, nullable=False, index=True)
    draw_date = Column(Date, nullable=False, index=True)
    numbers = Column(String(200), nullable=False)  # Comma-separated numbers
    winners_main = Column(Integer)
    winners_secondary = Column(Integer)
    winners_tertiary = Column(Integer)
    prize_main = Column(Float)
    prize_secondary = Column(Float)
    prize_tertiary = Column(Float)
    city = Column(String(200))
    checksum = Column(String(64), unique=True)
    created_at = Column(Date, default=datetime.now)


class DataCollector:
    """Main class for collecting lottery data"""
    
    def __init__(self, config_path: str = './config.yaml'):
        """
        Initialize the data collector
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.db_engine = self._init_database()
        self.session_maker = sessionmaker(bind=self.db_engine)
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
    
    def _init_database(self) -> create_engine:
        """Initialize database connection"""
        db_config = self.config['database']
        
        if db_config['type'] == 'sqlite':
            db_path = db_config['path']
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            engine = create_engine(f'sqlite:///{db_path}')
        else:
            # PostgreSQL support can be added here
            raise NotImplementedError("PostgreSQL support not implemented yet")
        
        Base.metadata.create_all(engine)
        logger.info("Database initialized successfully")
        return engine
    
    def _calculate_checksum(self, draw_number: int, numbers: List[int]) -> str:
        """
        Calculate checksum for data validation
        
        Args:
            draw_number: Draw/contest number
            numbers: List of drawn numbers
            
        Returns:
            SHA-256 checksum string
        """
        data = f"{draw_number}:{','.join(map(str, sorted(numbers)))}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _download_excel_data(self, url: str) -> pd.DataFrame:
        """
        Download lottery data from Excel file
        
        Args:
            url: URL to download Excel file from
            
        Returns:
            DataFrame with lottery data
        """
        try:
            ssl._create_default_https_context = ssl._create_unverified_context
            
            retry_config = self.config['data_collection']
            max_retries = retry_config['retry_attempts']
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"Downloading data from {url} (attempt {attempt + 1}/{max_retries})")
                    data = pd.read_excel(url)
                    logger.info(f"Successfully downloaded {len(data)} records")
                    return data
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"Download attempt {attempt + 1} failed: {e}")
                    
        except Exception as e:
            logger.error(f"Error downloading data: {e}")
            raise
    
    def _parse_lotofacil_data(self, df: pd.DataFrame) -> List[Dict]:
        """
        Parse Lotofácil specific data format
        
        Args:
            df: Raw DataFrame from Excel
            
        Returns:
            List of parsed lottery results
        """
        results = []
        
        # Column mapping
        ball_columns = [f'Bola{i}' for i in range(1, 16)]
        
        for _, row in df.iterrows():
            try:
                draw_number = int(row['Concurso'])
                draw_date = pd.to_datetime(row['Data Sorteio'])
                
                # Extract drawn numbers
                numbers = [int(row[col]) for col in ball_columns if col in row]
                numbers_str = ','.join(map(str, sorted(numbers)))
                
                # Calculate checksum
                checksum = self._calculate_checksum(draw_number, numbers)
                
                result = {
                    'lottery_type': 'lotofacil',
                    'draw_number': draw_number,
                    'draw_date': draw_date,
                    'numbers': numbers_str,
                    'winners_main': row.get('Ganhadores_15_Números', 0),
                    'winners_secondary': row.get('Ganhadores_14_Números', 0),
                    'winners_tertiary': row.get('Ganhadores_13_Números', 0),
                    'prize_main': row.get('Valor_Rateio_15_Números', 0.0),
                    'prize_secondary': row.get('Valor_Rateio_14_Números', 0.0),
                    'prize_tertiary': row.get('Valor_Rateio_13_Números', 0.0),
                    'city': row.get('Cidade', ''),
                    'checksum': checksum
                }
                results.append(result)
            except Exception as e:
                logger.warning(f"Error parsing row {row.get('Concurso', 'unknown')}: {e}")
                continue
        
        return results
    
    def _parse_megasena_data(self, df: pd.DataFrame) -> List[Dict]:
        """
        Parse Mega-Sena specific data format
        
        Args:
            df: Raw DataFrame from Excel
            
        Returns:
            List of parsed lottery results
        """
        results = []
        
        # Column mapping for Mega-Sena (6 balls)
        ball_columns = [f'Bola{i}' for i in range(1, 7)]
        
        for _, row in df.iterrows():
            try:
                draw_number = int(row['Concurso'])
                draw_date = pd.to_datetime(row['Data Sorteio'])
                
                # Extract drawn numbers
                numbers = [int(row[col]) for col in ball_columns if col in row]
                numbers_str = ','.join(map(str, sorted(numbers)))
                
                # Calculate checksum
                checksum = self._calculate_checksum(draw_number, numbers)
                
                result = {
                    'lottery_type': 'megasena',
                    'draw_number': draw_number,
                    'draw_date': draw_date,
                    'numbers': numbers_str,
                    'winners_main': row.get('Ganhadores_Sena', 0),
                    'winners_secondary': row.get('Ganhadores_Quina', 0),
                    'winners_tertiary': row.get('Ganhadores_Quadra', 0),
                    'prize_main': row.get('Valor_Rateio_Sena', 0.0),
                    'prize_secondary': row.get('Valor_Rateio_Quina', 0.0),
                    'prize_tertiary': row.get('Valor_Rateio_Quadra', 0.0),
                    'city': row.get('Cidade', ''),
                    'checksum': checksum
                }
                results.append(result)
            except Exception as e:
                logger.warning(f"Error parsing row {row.get('Concurso', 'unknown')}: {e}")
                continue
        
        return results
    
    def _parse_quina_data(self, df: pd.DataFrame) -> List[Dict]:
        """
        Parse Quina specific data format
        
        Args:
            df: Raw DataFrame from Excel
            
        Returns:
            List of parsed lottery results
        """
        results = []
        
        # Column mapping for Quina (5 balls)
        ball_columns = [f'Bola{i}' for i in range(1, 6)]
        
        for _, row in df.iterrows():
            try:
                draw_number = int(row['Concurso'])
                draw_date = pd.to_datetime(row['Data Sorteio'])
                
                # Extract drawn numbers
                numbers = [int(row[col]) for col in ball_columns if col in row]
                numbers_str = ','.join(map(str, sorted(numbers)))
                
                # Calculate checksum
                checksum = self._calculate_checksum(draw_number, numbers)
                
                result = {
                    'lottery_type': 'quina',
                    'draw_number': draw_number,
                    'draw_date': draw_date,
                    'numbers': numbers_str,
                    'winners_main': row.get('Ganhadores_Quina', 0),
                    'winners_secondary': row.get('Ganhadores_Quadra', 0),
                    'winners_tertiary': row.get('Ganhadores_Terno', 0),
                    'prize_main': row.get('Valor_Rateio_Quina', 0.0),
                    'prize_secondary': row.get('Valor_Rateio_Quadra', 0.0),
                    'prize_tertiary': row.get('Valor_Rateio_Terno', 0.0),
                    'city': row.get('Cidade', ''),
                    'checksum': checksum
                }
                results.append(result)
            except Exception as e:
                logger.warning(f"Error parsing row {row.get('Concurso', 'unknown')}: {e}")
                continue
        
        return results
    
    def update_lottery_data(self, lottery_type: str) -> Tuple[int, int]:
        """
        Update lottery data from official source
        
        Args:
            lottery_type: Type of lottery (lotofacil, megasena, quina, etc.)
            
        Returns:
            Tuple of (new_records, updated_records)
        """
        if lottery_type not in self.config['lotteries']:
            raise ValueError(f"Unknown lottery type: {lottery_type}")
        
        lottery_config = self.config['lotteries'][lottery_type]
        
        if not lottery_config['enabled']:
            logger.info(f"{lottery_type} is not enabled in configuration")
            return 0, 0
        
        # Download data
        url = lottery_config['api_url']
        df = self._download_excel_data(url)
        
        # Parse data based on lottery type
        if lottery_type == 'lotofacil':
            parsed_results = self._parse_lotofacil_data(df)
        elif lottery_type == 'megasena':
            parsed_results = self._parse_megasena_data(df)
        elif lottery_type == 'quina':
            parsed_results = self._parse_quina_data(df)
        else:
            logger.warning(f"Parser not implemented for {lottery_type}")
            return 0, 0
        
        # Store in database
        session = self.session_maker()
        new_count = 0
        updated_count = 0
        
        try:
            for result in parsed_results:
                # Check if record exists
                existing = session.query(LotteryResult).filter_by(
                    checksum=result['checksum']
                ).first()
                
                if existing is None:
                    # Insert new record
                    lottery_result = LotteryResult(**result)
                    session.add(lottery_result)
                    new_count += 1
                else:
                    # Update existing record if needed
                    updated_count += 1
            
            session.commit()
            logger.info(f"Updated {lottery_type}: {new_count} new, {updated_count} existing")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing data: {e}")
            raise
        finally:
            session.close()
        
        return new_count, updated_count
    
    def update_all_lotteries(self) -> Dict[str, Tuple[int, int]]:
        """
        Update all enabled lotteries
        
        Returns:
            Dictionary mapping lottery type to (new_records, updated_records)
        """
        results = {}
        
        for lottery_type, config in self.config['lotteries'].items():
            if config['enabled']:
                try:
                    results[lottery_type] = self.update_lottery_data(lottery_type)
                except Exception as e:
                    logger.error(f"Error updating {lottery_type}: {e}")
                    results[lottery_type] = (0, 0)
        
        return results
    
    def get_lottery_data(self, lottery_type: str, limit: Optional[int] = None) -> pd.DataFrame:
        """
        Retrieve lottery data from database
        
        Args:
            lottery_type: Type of lottery
            limit: Optional limit on number of records
            
        Returns:
            DataFrame with lottery results
        """
        session = self.session_maker()
        
        try:
            query = session.query(LotteryResult).filter_by(lottery_type=lottery_type)
            query = query.order_by(LotteryResult.draw_number.desc())
            
            if limit:
                query = query.limit(limit)
            
            results = query.all()
            
            # Convert to DataFrame
            data = []
            for result in results:
                data.append({
                    'draw_number': result.draw_number,
                    'draw_date': result.draw_date,
                    'numbers': result.numbers,
                    'winners_main': result.winners_main,
                    'winners_secondary': result.winners_secondary,
                    'winners_tertiary': result.winners_tertiary,
                    'prize_main': result.prize_main,
                    'prize_secondary': result.prize_secondary,
                    'prize_tertiary': result.prize_tertiary,
                })
            
            return pd.DataFrame(data)
            
        finally:
            session.close()
    
    def get_statistics(self, lottery_type: str) -> Dict:
        """
        Get basic statistics for a lottery type
        
        Args:
            lottery_type: Type of lottery
            
        Returns:
            Dictionary with statistics
        """
        session = self.session_maker()
        
        try:
            total_draws = session.query(LotteryResult).filter_by(
                lottery_type=lottery_type
            ).count()
            
            latest_draw = session.query(LotteryResult).filter_by(
                lottery_type=lottery_type
            ).order_by(LotteryResult.draw_number.desc()).first()
            
            stats = {
                'lottery_type': lottery_type,
                'total_draws': total_draws,
                'latest_draw_number': latest_draw.draw_number if latest_draw else 0,
                'latest_draw_date': latest_draw.draw_date if latest_draw else None,
            }
            
            return stats
            
        finally:
            session.close()


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Lottery Data Collector')
    parser.add_argument('--update', action='store_true', help='Update all lottery data')
    parser.add_argument('--lottery', type=str, help='Update specific lottery type')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--config', type=str, default='./config.yaml', help='Config file path')
    
    args = parser.parse_args()
    
    collector = DataCollector(config_path=args.config)
    
    if args.update:
        if args.lottery:
            new, updated = collector.update_lottery_data(args.lottery)
            print(f"\n{args.lottery.upper()} Updated:")
            print(f"  New records: {new}")
            print(f"  Existing records: {updated}")
        else:
            results = collector.update_all_lotteries()
            print("\nAll Lotteries Updated:")
            for lottery_type, (new, updated) in results.items():
                print(f"\n{lottery_type.upper()}:")
                print(f"  New records: {new}")
                print(f"  Existing records: {updated}")
    
    if args.stats:
        for lottery_type in collector.config['lotteries']:
            if collector.config['lotteries'][lottery_type]['enabled']:
                stats = collector.get_statistics(lottery_type)
                print(f"\n{lottery_type.upper()} Statistics:")
                print(f"  Total draws: {stats['total_draws']}")
                print(f"  Latest draw: #{stats['latest_draw_number']}")
                print(f"  Latest date: {stats['latest_draw_date']}")


if __name__ == '__main__':
    main()
