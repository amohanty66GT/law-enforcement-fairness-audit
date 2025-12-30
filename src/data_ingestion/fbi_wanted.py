"""
FBI Wanted API data ingestion module.
Fetches public wanted persons data from FBI's official API.
"""

import requests
import pandas as pd
import time
from datetime import datetime
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FBIWantedIngestion:
    """Handles FBI Wanted API data collection."""
    
    BASE_URL = "https://api.fbi.gov/wanted/v1/list"
    
    def __init__(self, delay: float = 1.0):
        self.delay = delay
        self.session = requests.Session()
        
    def fetch_wanted_data(self, page_size: int = 50, max_pages: Optional[int] = None) -> pd.DataFrame:
        """
        Fetch wanted persons data from FBI API.
        
        Args:
            page_size: Number of records per page
            max_pages: Maximum pages to fetch (None for all)
            
        Returns:
            DataFrame with wanted persons data
        """
        all_records = []
        page = 1
        
        while True:
            if max_pages and page > max_pages:
                break
                
            logger.info(f"Fetching page {page}")
            
            params = {
                'page': page,
                'pageSize': page_size
            }
            
            try:
                response = self.session.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                
                if 'items' not in data or not data['items']:
                    logger.info("No more data available")
                    break
                    
                all_records.extend(data['items'])
                
                # Check if we've reached the end
                if len(data['items']) < page_size:
                    break
                    
                page += 1
                time.sleep(self.delay)  # Rate limiting
                
            except requests.RequestException as e:
                logger.error(f"Error fetching page {page}: {e}")
                break
                
        logger.info(f"Collected {len(all_records)} records")
        return self._process_records(all_records)
    
    def _process_records(self, records: List[Dict]) -> pd.DataFrame:
        """Process raw API records into structured DataFrame."""
        processed = []
        
        for record in records:
            processed_record = {
                'uid': record.get('uid'),
                'title': record.get('title'),
                'description': record.get('description'),
                'subjects': record.get('subjects', []),
                'publication_date': record.get('publication'),
                'modified_date': record.get('modified'),
                'url': record.get('url'),
                'warning_message': record.get('warning_message'),
                'reward_text': record.get('reward_text'),
                'caution': record.get('caution'),
                'details': record.get('details'),
                'images': record.get('images', []),
                'files': record.get('files', [])
            }
            
            # Extract subject information
            if record.get('subjects'):
                subject = record['subjects'][0]  # Take first subject
                processed_record.update({
                    'name': subject.get('name'),
                    'sex': subject.get('sex'),
                    'race': subject.get('race'),
                    'nationality': subject.get('nationality'),
                    'date_of_birth': subject.get('date_of_birth'),
                    'place_of_birth': subject.get('place_of_birth'),
                    'hair': subject.get('hair'),
                    'eyes': subject.get('eyes'),
                    'height_min': subject.get('height_min'),
                    'height_max': subject.get('height_max'),
                    'weight': subject.get('weight'),
                    'aliases': subject.get('aliases', [])
                })
            
            processed.append(processed_record)
        
        df = pd.DataFrame(processed)
        
        # Convert date columns
        date_columns = ['publication_date', 'modified_date', 'date_of_birth']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Add derived features
        df['ingestion_date'] = datetime.now()
        df['case_age_days'] = (df['ingestion_date'] - df['publication_date']).dt.days
        
        return df

if __name__ == "__main__":
    ingestion = FBIWantedIngestion()
    df = ingestion.fetch_wanted_data(max_pages=5)  # Test with 5 pages
    print(f"Collected {len(df)} records")
    print(df.head())