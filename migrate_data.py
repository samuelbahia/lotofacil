"""
Migration utility to import existing lottery data into the new database
"""

import pandas as pd
from data_collector import DataCollector, LotteryResult
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_lotofacil_csv_to_db(csv_path: str = './base/resultados.csv',
                                 config_path: str = './config.yaml'):
    """
    Migrate existing Lotofácil CSV data to database
    
    Args:
        csv_path: Path to existing CSV file
        config_path: Path to configuration file
    """
    logger.info(f"Starting migration from {csv_path}")
    
    # Initialize collector
    collector = DataCollector(config_path)
    
    # Read CSV
    df = pd.read_csv(csv_path, sep=';', encoding='utf8')
    logger.info(f"Loaded {len(df)} records from CSV")
    
    # Process records
    session = collector.session_maker()
    new_count = 0
    
    try:
        for _, row in df.iterrows():
            try:
                # Extract draw number
                draw_number = int(row['Concurso'])
                
                # Extract date
                draw_date = pd.to_datetime(row['Data Sorteio'], errors='coerce')
                
                # Extract numbers
                numbers = []
                for i in range(1, 16):
                    col_name = f'B{i}'
                    if col_name in row:
                        numbers.append(int(row[col_name]))
                
                numbers_str = ','.join(map(str, sorted(numbers)))
                
                # Calculate checksum
                checksum = collector._calculate_checksum(draw_number, numbers)
                
                # Check if exists
                existing = session.query(LotteryResult).filter_by(
                    checksum=checksum
                ).first()
                
                if existing is None:
                    # Create new record
                    result = LotteryResult(
                        lottery_type='lotofacil',
                        draw_number=draw_number,
                        draw_date=draw_date,
                        numbers=numbers_str,
                        winners_main=row.get('Ganhou', 0),
                        checksum=checksum
                    )
                    session.add(result)
                    new_count += 1
                    
                    if new_count % 100 == 0:
                        logger.info(f"Processed {new_count} new records...")
                        
            except Exception as e:
                logger.warning(f"Error processing row {row.get('Concurso', 'unknown')}: {e}")
                continue
        
        session.commit()
        logger.info(f"Migration complete: {new_count} new records added")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        session.close()
    
    return new_count


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate existing lottery data')
    parser.add_argument('--csv', type=str, default='./base/resultados.csv',
                       help='Path to CSV file')
    parser.add_argument('--config', type=str, default='./config.yaml',
                       help='Config file path')
    
    args = parser.parse_args()
    
    count = migrate_lotofacil_csv_to_db(args.csv, args.config)
    print(f"\nSuccessfully migrated {count} records to database!")
