"""
Configuration settings for the fairness and bias audit system.
"""

import os
from typing import Dict, List

# Database Configuration
DATABASE_CONFIG = {
    'default_type': 'duckdb',
    'postgresql': {
        'url': os.getenv('DATABASE_URL', 'postgresql://username:password@localhost:5432/fairness_audit'),
        'pool_size': 5,
        'max_overflow': 10
    },
    'duckdb': {
        'path': os.getenv('DUCKDB_PATH', 'data/fairness_audit.db'),
        'memory_limit': '2GB',
        'threads': 4
    }
}

# API Configuration
API_CONFIG = {
    'fbi_wanted': {
        'base_url': 'https://api.fbi.gov/wanted/v1/list',
        'rate_limit_delay': float(os.getenv('FBI_API_DELAY', '1.0')),
        'timeout': 30,
        'max_retries': 3
    },
    'fbi_cde': {
        'base_url': 'https://api.usa.gov/crime/fbi/cde',
        'timeout': 30,
        'max_retries': 3
    }
}

# Analysis Configuration
ANALYSIS_CONFIG = {
    'confidence_level': float(os.getenv('CONFIDENCE_LEVEL', '0.95')),
    'min_sample_size': int(os.getenv('MIN_SAMPLE_SIZE', '100')),
    'bias_thresholds': {
        'over_representation': 1.2,  # 20% over expected
        'under_representation': 0.8,  # 20% under expected
        'significance_level': 0.05
    },
    'temporal_analysis': {
        'min_years': 2,
        'trend_threshold': 0.1  # Minimum correlation for trend detection
    }
}

# Feature Engineering Configuration
FEATURE_CONFIG = {
    'crime_categories': {
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
    },
    'regional_mapping': {
        'Northeast': ['CT', 'ME', 'MA', 'NH', 'NJ', 'NY', 'PA', 'RI', 'VT'],
        'Southeast': ['AL', 'AR', 'FL', 'GA', 'KY', 'LA', 'MS', 'NC', 'SC', 'TN', 'VA', 'WV'],
        'Midwest': ['IL', 'IN', 'IA', 'KS', 'MI', 'MN', 'MO', 'NE', 'ND', 'OH', 'SD', 'WI'],
        'Southwest': ['AZ', 'NM', 'OK', 'TX'],
        'West': ['AK', 'CA', 'CO', 'HI', 'ID', 'MT', 'NV', 'OR', 'UT', 'WA', 'WY']
    },
    'case_age_categories': {
        'Recent': (0, 30),      # Less than 1 month
        'Medium': (30, 365),    # 1-12 months
        'Long': (365, 1825),    # 1-5 years
        'Very Long': (1825, float('inf'))  # More than 5 years
    }
}

# Visualization Configuration
VISUALIZATION_CONFIG = {
    'color_palettes': {
        'primary': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
        'bias_detection': {
            'over_represented': '#ff6b6b',
            'under_represented': '#4ecdc4',
            'normal': '#95a5a6'
        },
        'sequential': 'Blues',
        'diverging': 'RdBu_r'
    },
    'chart_defaults': {
        'height': 400,
        'font_size': 12,
        'title_font_size': 16,
        'margin': {'l': 50, 'r': 50, 't': 50, 'b': 50}
    }
}

# Dashboard Configuration
DASHBOARD_CONFIG = {
    'title': 'Law Enforcement Data Fairness & Bias Audit',
    'page_icon': '⚖️',
    'layout': 'wide',
    'sidebar_state': 'expanded',
    'cache_ttl': 3600,  # 1 hour cache
    'max_upload_size': 200  # MB
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_handler': {
        'enabled': True,
        'filename': 'logs/fairness_audit.log',
        'max_bytes': 10 * 1024 * 1024,  # 10MB
        'backup_count': 5
    }
}

# Data Quality Configuration
DATA_QUALITY_CONFIG = {
    'required_fields': ['uid', 'title', 'publication_date'],
    'validation_rules': {
        'uid': {'type': str, 'not_null': True, 'unique': True},
        'publication_date': {'type': 'datetime', 'not_null': True},
        'case_age_days': {'type': int, 'min_value': 0}
    },
    'cleaning_rules': {
        'remove_duplicates': True,
        'standardize_states': True,
        'normalize_text': True
    }
}

# Export Configuration
EXPORT_CONFIG = {
    'formats': ['json', 'csv', 'xlsx'],
    'compression': True,
    'include_metadata': True,
    'timestamp_format': '%Y%m%d_%H%M%S'
}

# Security Configuration
SECURITY_CONFIG = {
    'anonymization': {
        'enabled': True,
        'fields_to_anonymize': ['name', 'aliases'],
        'hash_algorithm': 'sha256'
    },
    'data_retention': {
        'max_age_days': 365,
        'cleanup_enabled': False
    }
}

def get_config(section: str) -> Dict:
    """Get configuration for a specific section."""
    
    config_map = {
        'database': DATABASE_CONFIG,
        'api': API_CONFIG,
        'analysis': ANALYSIS_CONFIG,
        'features': FEATURE_CONFIG,
        'visualization': VISUALIZATION_CONFIG,
        'dashboard': DASHBOARD_CONFIG,
        'logging': LOGGING_CONFIG,
        'data_quality': DATA_QUALITY_CONFIG,
        'export': EXPORT_CONFIG,
        'security': SECURITY_CONFIG
    }
    
    return config_map.get(section, {})

def validate_config():
    """Validate configuration settings."""
    
    errors = []
    
    # Check required environment variables
    required_env_vars = []  # Add any required env vars here
    
    for var in required_env_vars:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")
    
    # Validate confidence level
    confidence = ANALYSIS_CONFIG['confidence_level']
    if not 0.5 <= confidence <= 0.99:
        errors.append(f"Invalid confidence level: {confidence}. Must be between 0.5 and 0.99")
    
    # Validate sample size
    min_sample = ANALYSIS_CONFIG['min_sample_size']
    if min_sample < 10:
        errors.append(f"Minimum sample size too small: {min_sample}. Must be at least 10")
    
    if errors:
        raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    return True

if __name__ == "__main__":
    # Test configuration
    try:
        validate_config()
        print("Configuration validation passed")
        
        # Print sample configuration
        print("\nSample configuration sections:")
        for section in ['database', 'analysis', 'visualization']:
            config = get_config(section)
            print(f"\n{section.upper()}:")
            for key, value in config.items():
                print(f"  {key}: {value}")
                
    except ValueError as e:
        print(f"Configuration error: {e}")