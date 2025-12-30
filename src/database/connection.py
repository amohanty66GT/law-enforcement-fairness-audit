"""
Database connection and management utilities.
Supports both PostgreSQL and DuckDB for different deployment scenarios.
"""

import os
import pandas as pd
from typing import Optional, Dict, Any
import logging
from sqlalchemy import create_engine, text
import duckdb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, db_type: str = "duckdb", connection_string: Optional[str] = None):
        """
        Initialize database manager.
        
        Args:
            db_type: Either 'postgresql' or 'duckdb'
            connection_string: Database connection string (optional)
        """
        self.db_type = db_type.lower()
        self.connection_string = connection_string or self._get_default_connection()
        self.engine = None
        self.duckdb_conn = None
        
        self._initialize_connection()
    
    def _get_default_connection(self) -> str:
        """Get default connection string based on environment."""
        
        if self.db_type == "postgresql":
            return os.getenv(
                "DATABASE_URL", 
                "postgresql://username:password@localhost:5432/fairness_audit"
            )
        elif self.db_type == "duckdb":
            return os.getenv("DUCKDB_PATH", "data/fairness_audit.db")
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")
    
    def _initialize_connection(self):
        """Initialize database connection."""
        
        try:
            if self.db_type == "postgresql":
                self.engine = create_engine(self.connection_string)
                logger.info("PostgreSQL connection initialized")
                
            elif self.db_type == "duckdb":
                # Ensure data directory exists
                os.makedirs(os.path.dirname(self.connection_string), exist_ok=True)
                self.duckdb_conn = duckdb.connect(self.connection_string)
                logger.info(f"DuckDB connection initialized: {self.connection_string}")
                
        except Exception as e:
            logger.error(f"Failed to initialize {self.db_type} connection: {e}")
            raise
    
    def create_tables(self):
        """Create necessary tables for the fairness audit system."""
        
        tables = {
            'wanted_persons': '''
                CREATE TABLE IF NOT EXISTS wanted_persons (
                    uid VARCHAR PRIMARY KEY,
                    title TEXT,
                    description TEXT,
                    name VARCHAR,
                    sex VARCHAR,
                    race VARCHAR,
                    nationality VARCHAR,
                    date_of_birth DATE,
                    place_of_birth TEXT,
                    publication_date TIMESTAMP,
                    modified_date TIMESTAMP,
                    ingestion_date TIMESTAMP,
                    case_age_days INTEGER,
                    reward_text TEXT,
                    warning_message TEXT,
                    url TEXT,
                    
                    -- Engineered features
                    birth_state VARCHAR,
                    birth_region VARCHAR,
                    crime_family VARCHAR,
                    case_age_category VARCHAR,
                    publication_year INTEGER,
                    publication_quarter INTEGER,
                    has_reward BOOLEAN,
                    has_images BOOLEAN
                )
            ''',
            
            'crime_statistics': '''
                CREATE TABLE IF NOT EXISTS crime_statistics (
                    id SERIAL PRIMARY KEY,
                    year INTEGER,
                    state VARCHAR,
                    offense_type VARCHAR,
                    crime_family VARCHAR,
                    count INTEGER,
                    rate_per_100k FLOAT,
                    source VARCHAR,
                    ingestion_date TIMESTAMP
                )
            ''',
            
            'bias_analysis_results': '''
                CREATE TABLE IF NOT EXISTS bias_analysis_results (
                    id SERIAL PRIMARY KEY,
                    analysis_type VARCHAR,
                    analysis_date TIMESTAMP,
                    confidence_level FLOAT,
                    test_statistic FLOAT,
                    p_value FLOAT,
                    significant_bias BOOLEAN,
                    interpretation TEXT,
                    metadata JSON,
                    sample_size INTEGER
                )
            '''
        }
        
        for table_name, create_sql in tables.items():
            try:
                if self.db_type == "postgresql":
                    with self.engine.connect() as conn:
                        conn.execute(text(create_sql))
                        conn.commit()
                        
                elif self.db_type == "duckdb":
                    # Adjust SQL for DuckDB
                    duckdb_sql = create_sql.replace('SERIAL PRIMARY KEY', 'INTEGER PRIMARY KEY')
                    duckdb_sql = duckdb_sql.replace('JSON', 'TEXT')  # DuckDB doesn't have JSON type
                    self.duckdb_conn.execute(duckdb_sql)
                
                logger.info(f"Table '{table_name}' created/verified")
                
            except Exception as e:
                logger.error(f"Error creating table '{table_name}': {e}")
                raise
    
    def save_wanted_data(self, df: pd.DataFrame, if_exists: str = 'append'):
        """
        Save wanted persons data to database.
        
        Args:
            df: DataFrame with wanted persons data
            if_exists: How to handle existing data ('append', 'replace', 'fail')
        """
        try:
            if self.db_type == "postgresql":
                df.to_sql('wanted_persons', self.engine, if_exists=if_exists, index=False)
                
            elif self.db_type == "duckdb":
                if if_exists == 'replace':
                    self.duckdb_conn.execute("DROP TABLE IF EXISTS wanted_persons")
                    self.create_tables()  # Recreate table
                
                # Insert data
                self.duckdb_conn.register('df_temp', df)
                self.duckdb_conn.execute("""
                    INSERT INTO wanted_persons 
                    SELECT * FROM df_temp
                """)
            
            logger.info(f"Saved {len(df)} wanted persons records")
            
        except Exception as e:
            logger.error(f"Error saving wanted data: {e}")
            raise
    
    def save_crime_data(self, df: pd.DataFrame, if_exists: str = 'append'):
        """Save crime statistics data to database."""
        
        try:
            if self.db_type == "postgresql":
                df.to_sql('crime_statistics', self.engine, if_exists=if_exists, index=False)
                
            elif self.db_type == "duckdb":
                if if_exists == 'replace':
                    self.duckdb_conn.execute("DROP TABLE IF EXISTS crime_statistics")
                    self.create_tables()
                
                self.duckdb_conn.register('df_temp', df)
                self.duckdb_conn.execute("""
                    INSERT INTO crime_statistics 
                    SELECT * FROM df_temp
                """)
            
            logger.info(f"Saved {len(df)} crime statistics records")
            
        except Exception as e:
            logger.error(f"Error saving crime data: {e}")
            raise
    
    def save_analysis_results(self, results: Dict[str, Any], analysis_type: str):
        """Save bias analysis results to database."""
        
        analysis_record = {
            'analysis_type': analysis_type,
            'analysis_date': pd.Timestamp.now(),
            'confidence_level': results.get('confidence_level'),
            'test_statistic': results.get('chi_square_statistic') or results.get('anova_f_statistic'),
            'p_value': results.get('p_value'),
            'significant_bias': results.get('significant_bias'),
            'interpretation': results.get('interpretation'),
            'metadata': str(results),  # Store full results as text
            'sample_size': results.get('sample_size')
        }
        
        try:
            analysis_df = pd.DataFrame([analysis_record])
            
            if self.db_type == "postgresql":
                analysis_df.to_sql('bias_analysis_results', self.engine, if_exists='append', index=False)
                
            elif self.db_type == "duckdb":
                self.duckdb_conn.register('analysis_temp', analysis_df)
                self.duckdb_conn.execute("""
                    INSERT INTO bias_analysis_results 
                    SELECT * FROM analysis_temp
                """)
            
            logger.info(f"Saved {analysis_type} analysis results")
            
        except Exception as e:
            logger.error(f"Error saving analysis results: {e}")
            raise
    
    def load_wanted_data(self, filters: Optional[Dict] = None) -> pd.DataFrame:
        """Load wanted persons data from database."""
        
        query = "SELECT * FROM wanted_persons"
        
        if filters:
            conditions = []
            for key, value in filters.items():
                if isinstance(value, list):
                    conditions.append(f"{key} IN ({','.join(['?' for _ in value])})")
                else:
                    conditions.append(f"{key} = ?")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        try:
            if self.db_type == "postgresql":
                return pd.read_sql(query, self.engine)
                
            elif self.db_type == "duckdb":
                return self.duckdb_conn.execute(query).df()
                
        except Exception as e:
            logger.error(f"Error loading wanted data: {e}")
            return pd.DataFrame()
    
    def load_crime_data(self, filters: Optional[Dict] = None) -> pd.DataFrame:
        """Load crime statistics data from database."""
        
        query = "SELECT * FROM crime_statistics"
        
        if filters:
            conditions = []
            for key, value in filters.items():
                if isinstance(value, list):
                    conditions.append(f"{key} IN ({','.join(['?' for _ in value])})")
                else:
                    conditions.append(f"{key} = ?")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        try:
            if self.db_type == "postgresql":
                return pd.read_sql(query, self.engine)
                
            elif self.db_type == "duckdb":
                return self.duckdb_conn.execute(query).df()
                
        except Exception as e:
            logger.error(f"Error loading crime data: {e}")
            return pd.DataFrame()
    
    def get_analysis_history(self) -> pd.DataFrame:
        """Get history of bias analysis results."""
        
        query = "SELECT * FROM bias_analysis_results ORDER BY analysis_date DESC"
        
        try:
            if self.db_type == "postgresql":
                return pd.read_sql(query, self.engine)
                
            elif self.db_type == "duckdb":
                return self.duckdb_conn.execute(query).df()
                
        except Exception as e:
            logger.error(f"Error loading analysis history: {e}")
            return pd.DataFrame()
    
    def close(self):
        """Close database connections."""
        
        try:
            if self.engine:
                self.engine.dispose()
                logger.info("PostgreSQL connection closed")
                
            if self.duckdb_conn:
                self.duckdb_conn.close()
                logger.info("DuckDB connection closed")
                
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")

if __name__ == "__main__":
    # Test database operations
    db = DatabaseManager(db_type="duckdb")
    
    # Create tables
    db.create_tables()
    
    # Test with sample data
    sample_data = pd.DataFrame({
        'uid': ['test_001', 'test_002'],
        'title': ['Test Case 1', 'Test Case 2'],
        'description': ['Sample description 1', 'Sample description 2'],
        'publication_date': pd.to_datetime(['2023-01-01', '2023-06-01']),
        'ingestion_date': pd.Timestamp.now(),
        'crime_family': ['Violent', 'White Collar'],
        'birth_state': ['CA', 'TX']
    })
    
    # Save and load data
    db.save_wanted_data(sample_data)
    loaded_data = db.load_wanted_data()
    
    print(f"Saved and loaded {len(loaded_data)} records")
    print(loaded_data.head())
    
    db.close()