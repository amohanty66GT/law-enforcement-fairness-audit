"""
Feature engineering for fairness and bias analysis.
Creates derived features for geographic, temporal, and categorical analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeatureEngineer:
    """Handles feature engineering for bias analysis."""
    
    def __init__(self):
        self.state_populations = self._load_state_populations()
        self.crime_categories = self._define_crime_categories()
    
    def engineer_features(self, wanted_df: pd.DataFrame, crime_df: pd.DataFrame = None) -> pd.DataFrame:
        """
        Create analysis-ready features from raw data.
        
        Args:
            wanted_df: FBI wanted persons data
            crime_df: FBI crime statistics data (optional)
            
        Returns:
            DataFrame with engineered features
        """
        df = wanted_df.copy()
        
        # Geographic features
        df = self._add_geographic_features(df)
        
        # Temporal features
        df = self._add_temporal_features(df)
        
        # Crime categorization
        df = self._add_crime_categories(df)
        
        # Weapon analysis features
        df = self._add_weapon_features(df)
        
        # Serious crime flagging
        df = self._add_severity_flags(df)
        
        # Case persistence features
        df = self._add_persistence_features(df)
        
        # Bias detection features
        if crime_df is not None:
            df = self._add_baseline_comparisons(df, crime_df)
        
        logger.info(f"Feature engineering complete. Shape: {df.shape}")
        return df
    
    def _add_geographic_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add geographic analysis features."""
        
        # Extract state from place_of_birth or other location fields
        def extract_state(location_text):
            if pd.isna(location_text):
                return None
            
            # Simple state extraction (could be enhanced with NLP)
            state_codes = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
                          'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
                          'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
                          'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
                          'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
            
            location_upper = str(location_text).upper()
            for state in state_codes:
                if state in location_upper:
                    return state
            return 'UNKNOWN'
        
        df['birth_state'] = df['place_of_birth'].apply(extract_state)
        
        # Add population-based features
        df['birth_state_population'] = df['birth_state'].map(self.state_populations)
        
        # Regional groupings
        region_mapping = {
            'Northeast': ['CT', 'ME', 'MA', 'NH', 'NJ', 'NY', 'PA', 'RI', 'VT'],
            'Southeast': ['AL', 'AR', 'FL', 'GA', 'KY', 'LA', 'MS', 'NC', 'SC', 'TN', 'VA', 'WV'],
            'Midwest': ['IL', 'IN', 'IA', 'KS', 'MI', 'MN', 'MO', 'NE', 'ND', 'OH', 'SD', 'WI'],
            'Southwest': ['AZ', 'NM', 'OK', 'TX'],
            'West': ['AK', 'CA', 'CO', 'HI', 'ID', 'MT', 'NV', 'OR', 'UT', 'WA', 'WY'],
            'Other': ['UNKNOWN']
        }
        
        def get_region(state):
            for region, states in region_mapping.items():
                if state in states:
                    return region
            return 'Other'
        
        df['birth_region'] = df['birth_state'].apply(get_region)
        
        return df
    
    def _add_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add temporal analysis features."""
        
        # Publication date features
        df['publication_year'] = df['publication_date'].dt.year
        df['publication_quarter'] = df['publication_date'].dt.quarter
        df['publication_month'] = df['publication_date'].dt.month
        
        # Case age features
        df['case_age_months'] = df['case_age_days'] / 30.44
        df['case_age_years'] = df['case_age_days'] / 365.25
        
        # Age categories
        def categorize_case_age(days):
            if pd.isna(days):
                return 'Unknown'
            elif days < 30:
                return 'Recent (< 1 month)'
            elif days < 365:
                return 'Medium (1-12 months)'
            elif days < 1825:  # 5 years
                return 'Long (1-5 years)'
            else:
                return 'Very Long (> 5 years)'
        
        df['case_age_category'] = df['case_age_days'].apply(categorize_case_age)
        
        return df
    
    def _add_crime_categories(self, df: pd.DataFrame) -> pd.DataFrame:
        """Categorize crimes for analysis."""
        
        def categorize_crime(title, description):
            text = f"{title} {description}".lower()
            
            for category, keywords in self.crime_categories.items():
                if any(keyword in text for keyword in keywords):
                    return category
            return 'Other'
        
        df['crime_family'] = df.apply(
            lambda row: categorize_crime(
                str(row.get('title', '')), 
                str(row.get('description', ''))
            ), axis=1
        )
        
        return df
    
    def _add_weapon_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add weapon categorization features for serious crimes analysis."""
        
        # Extract weapon information from title and description
        def extract_weapon_info(title, description):
            text = f"{title} {description}".lower()
            
            # Look for weapon mentions
            weapon_keywords = {
                'firearm': [
                    'gun', 'firearm', 'pistol', 'rifle', 'shotgun', 'revolver', 
                    'weapon', 'armed', 'shooting', 'shot', 'bullet', 'ammunition',
                    'handgun', 'automatic', 'semi-automatic', 'caliber', '.22', '.38', 
                    '.45', '9mm', 'ak-47', 'ar-15', 'glock'
                ],
                'knife': [
                    'knife', 'blade', 'stabbing', 'stabbed', 'cut', 'cutting',
                    'machete', 'sword', 'dagger', 'razor', 'sharp object'
                ],
                'blunt_object': [
                    'bat', 'club', 'hammer', 'pipe', 'stick', 'bludgeon',
                    'blunt object', 'beating', 'beaten', 'struck with'
                ]
            }
            
            # Check for weapon mentions
            for category, keywords in weapon_keywords.items():
                if any(keyword in text for keyword in keywords):
                    return text, category
            
            # Check for explicit "no weapon" mentions
            no_weapon_keywords = ['unarmed', 'no weapon', 'without weapon']
            if any(keyword in text for keyword in no_weapon_keywords):
                return text, 'none'
            
            return text, 'unknown'
        
        # Apply weapon extraction
        weapon_data = df.apply(
            lambda row: extract_weapon_info(
                str(row.get('title', '')), 
                str(row.get('description', ''))
            ), axis=1
        )
        
        df['weapon_raw'] = weapon_data.apply(lambda x: x[0])
        df['weapon_category'] = weapon_data.apply(lambda x: x[1])
        
        return df
    
    def _add_severity_flags(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add severity flags for serious crimes."""
        
        # Define serious crimes
        serious_crime_keywords = [
            'murder', 'homicide', 'manslaughter', 'killing', 'killed',
            'aggravated assault', 'assault with deadly weapon',
            'armed robbery', 'robbery', 'bank robbery',
            'kidnapping', 'abduction',
            'rape', 'sexual assault',
            'terrorism', 'terrorist attack',
            'shooting', 'mass shooting'
        ]
        
        def is_serious_crime(title, description, crime_family):
            text = f"{title} {description}".lower()
            
            # Check for serious crime keywords
            if any(keyword in text for keyword in serious_crime_keywords):
                return True
            
            # Check crime family
            if crime_family in ['Violent', 'Terrorism']:
                return True
            
            return False
        
        df['severity_flag'] = df.apply(
            lambda row: is_serious_crime(
                str(row.get('title', '')),
                str(row.get('description', '')),
                row.get('crime_family', '')
            ), axis=1
        )
        
        # Add public notice flag (all wanted persons data is public notice)
        df['public_notice_flag'] = True
        
        return df
    
    def _add_persistence_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add features related to case persistence on wanted lists."""
        
        # Time since last modification
        df['days_since_modified'] = (df['ingestion_date'] - df['modified_date']).dt.days
        
        # Activity indicators
        df['recently_updated'] = df['days_since_modified'] < 30
        df['has_reward'] = df['reward_text'].notna()
        df['has_images'] = df['images'].apply(lambda x: len(x) > 0 if isinstance(x, list) else False)
        
        return df
    
    def _add_baseline_comparisons(self, df: pd.DataFrame, crime_df: pd.DataFrame) -> pd.DataFrame:
        """Add baseline crime statistics for comparison."""
        
        # Aggregate crime data by category and region
        crime_summary = crime_df.groupby(['crime_family', 'year']).agg({
            'count': 'sum',
            'rate_per_100k': 'mean'
        }).reset_index()
        
        # Merge with wanted data for comparison
        df = df.merge(
            crime_summary,
            left_on=['crime_family', 'publication_year'],
            right_on=['crime_family', 'year'],
            how='left',
            suffixes=('', '_baseline')
        )
        
        return df
    
    def _define_crime_categories(self) -> Dict[str, List[str]]:
        """Define crime category mappings."""
        return {
            'Violent': [
                'murder', 'homicide', 'assault', 'robbery', 'rape', 'kidnapping',
                'domestic violence', 'manslaughter', 'shooting'
            ],
            'White Collar': [
                'fraud', 'embezzlement', 'money laundering', 'tax evasion',
                'securities fraud', 'wire fraud', 'mail fraud', 'bribery',
                'corruption', 'insider trading'
            ],
            'Drug Related': [
                'drug trafficking', 'narcotics', 'cocaine', 'heroin', 'fentanyl',
                'methamphetamine', 'drug distribution', 'drug conspiracy'
            ],
            'Cyber Crime': [
                'computer fraud', 'hacking', 'identity theft', 'cyber',
                'internet fraud', 'phishing', 'ransomware'
            ],
            'Organized Crime': [
                'racketeering', 'rico', 'organized crime', 'conspiracy',
                'criminal enterprise', 'gang'
            ],
            'Terrorism': [
                'terrorism', 'terrorist', 'bombing', 'explosive',
                'national security', 'espionage'
            ]
        }
    
    def _load_state_populations(self) -> Dict[str, int]:
        """Load state population data for normalization."""
        # 2020 Census approximate populations (in millions)
        return {
            'CA': 39.5, 'TX': 29.1, 'FL': 21.5, 'NY': 19.8, 'PA': 13.0,
            'IL': 12.7, 'OH': 11.8, 'GA': 10.7, 'NC': 10.4, 'MI': 10.0,
            'NJ': 9.3, 'VA': 8.6, 'WA': 7.6, 'AZ': 7.3, 'MA': 7.0,
            'TN': 6.9, 'IN': 6.8, 'MO': 6.2, 'MD': 6.2, 'WI': 5.9,
            'CO': 5.8, 'MN': 5.7, 'SC': 5.1, 'AL': 5.0, 'LA': 4.7,
            'KY': 4.5, 'OR': 4.2, 'OK': 4.0, 'CT': 3.6, 'UT': 3.3,
            'IA': 3.2, 'NV': 3.1, 'AR': 3.0, 'MS': 2.9, 'KS': 2.9,
            'NM': 2.1, 'NE': 1.9, 'ID': 1.8, 'WV': 1.8, 'HI': 1.4,
            'NH': 1.4, 'ME': 1.4, 'MT': 1.1, 'RI': 1.1, 'DE': 1.0,
            'SD': 0.9, 'ND': 0.8, 'AK': 0.7, 'VT': 0.6, 'WY': 0.6
        }

if __name__ == "__main__":
    # Test feature engineering
    sample_data = pd.DataFrame({
        'title': ['Bank Fraud', 'Armed Robbery'],
        'description': ['Wire fraud scheme', 'Violent robbery'],
        'place_of_birth': ['Los Angeles, CA', 'Houston, TX'],
        'publication_date': pd.to_datetime(['2023-01-15', '2023-06-20']),
        'modified_date': pd.to_datetime(['2023-01-15', '2023-07-01']),
        'ingestion_date': pd.to_datetime(['2023-12-01', '2023-12-01']),
        'case_age_days': [320, 164],
        'reward_text': ['$10,000', None],
        'images': [['img1.jpg'], []]
    })
    
    engineer = FeatureEngineer()
    result = engineer.engineer_features(sample_data)
    print(result[['crime_family', 'birth_region', 'case_age_category']].head())