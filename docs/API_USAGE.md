# API Usage Guide

## Overview

This project integrates with several public APIs to collect law enforcement data for fairness analysis.

## Supported APIs

### 1. FBI Wanted API

**Endpoint**: `https://api.fbi.gov/wanted/v1/list`
**Documentation**: [FBI API Docs](https://www.fbi.gov/wanted/api)

```python
from src.data_ingestion.fbi_wanted import FBIWantedIngestion

# Initialize ingestion
ingestion = FBIWantedIngestion()

# Fetch data
df = ingestion.fetch_wanted_data(max_pages=10)
print(f"Collected {len(df)} records")
```

**Rate Limiting**: 1 request per second (configurable)
**Authentication**: None required (public API)

### 2. FBI Crime Data Explorer

**Endpoint**: `https://api.usa.gov/crime/fbi/cde`
**Documentation**: [CDE API Docs](https://crime-data-explorer.fr.cloud.gov/pages/api)

```python
from src.data_ingestion.fbi_crime_data import FBICrimeDataIngestion

# Initialize ingestion
ingestion = FBICrimeDataIngestion()

# Fetch offense data
df = ingestion.fetch_offense_data([2020, 2021, 2022, 2023])
print(f"Collected {len(df)} crime records")
```

**Rate Limiting**: Standard API limits
**Authentication**: None required

### 3. City Open Data APIs

Examples of supported city APIs:

#### LAPD Crime Data
```python
# Example for LAPD data integration
import requests
import pandas as pd

url = "https://data.lacity.org/resource/2nrs-mtv8.json"
response = requests.get(url, params={"$limit": 1000})
data = response.json()
df = pd.DataFrame(data)
```

#### Pittsburgh Police Data
```python
# Example for Pittsburgh data
url = "https://data.wprdc.org/api/action/datastore_search"
params = {
    "resource_id": "044f2016-1dfd-4ab0-bc1e-065da05fca2e",
    "limit": 1000
}
response = requests.get(url, params=params)
```

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# API Configuration
FBI_API_DELAY=1.0
CITY_DATA_API_KEY=your_api_key_here

# Rate Limiting
MAX_REQUESTS_PER_MINUTE=60
REQUEST_TIMEOUT=30

# Data Quality
MIN_SAMPLE_SIZE=100
CONFIDENCE_LEVEL=0.95
```

### Custom API Integration

To add a new data source:

1. **Create ingestion module**:
```python
# src/data_ingestion/your_api.py
class YourAPIIngestion:
    def __init__(self):
        self.base_url = "https://api.example.com"
    
    def fetch_data(self):
        # Implementation here
        pass
```

2. **Add to analysis pipeline**:
```python
# scripts/run_simple_analysis.py
from src.data_ingestion.your_api import YourAPIIngestion

# In main function
your_ingestion = YourAPIIngestion()
your_data = your_ingestion.fetch_data()
```

## Data Processing Pipeline

### 1. Raw Data Collection
```python
# Collect from multiple sources
fbi_data = fbi_ingestion.fetch_wanted_data()
crime_data = crime_ingestion.fetch_offense_data()
city_data = city_ingestion.fetch_local_data()
```

### 2. Data Standardization
```python
# Standardize column names and formats
standardized_data = standardize_schema(raw_data)
```

### 3. Feature Engineering
```python
from src.data_processing.feature_engineering import FeatureEngineer

engineer = FeatureEngineer()
processed_data = engineer.engineer_features(standardized_data)
```

### 4. Quality Validation
```python
# Validate data quality
quality_report = validate_data_quality(processed_data)
```

## Error Handling

### Common API Errors

**1. Rate Limiting**
```python
import time
from requests.exceptions import HTTPError

try:
    response = requests.get(url)
    response.raise_for_status()
except HTTPError as e:
    if e.response.status_code == 429:
        # Rate limited - wait and retry
        time.sleep(60)
        response = requests.get(url)
```

**2. Network Timeouts**
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)
```

**3. Data Validation**
```python
def validate_api_response(data):
    required_fields = ['uid', 'title', 'publication_date']
    
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    return True
```

## Best Practices

### 1. Respectful API Usage
- Follow rate limits
- Cache responses when appropriate
- Use appropriate user agents
- Monitor API health

### 2. Data Privacy
- Only collect publicly available data
- Avoid personal identifiers
- Implement data retention policies
- Document data sources

### 3. Error Recovery
- Implement exponential backoff
- Log all API interactions
- Graceful degradation for missing data
- Validate data integrity

### 4. Performance Optimization
- Use connection pooling
- Implement parallel requests (carefully)
- Cache frequently accessed data
- Monitor memory usage

## Monitoring and Logging

### API Health Monitoring
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def monitor_api_health(api_name, response):
    logger.info(f"{api_name} API - Status: {response.status_code}, "
                f"Response time: {response.elapsed.total_seconds():.2f}s")
```

### Data Quality Metrics
```python
def log_data_quality(df, source):
    logger.info(f"{source} - Records: {len(df)}, "
                f"Completeness: {df.notna().mean().mean():.2%}, "
                f"Duplicates: {df.duplicated().sum()}")
```

## Troubleshooting

### Common Issues

1. **SSL Certificate Errors**: Use `verify=False` for testing (not production)
2. **JSON Parsing Errors**: Validate response content type
3. **Memory Issues**: Process data in chunks
4. **Timeout Errors**: Increase timeout values or implement retry logic

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Run with verbose output:
```bash
python scripts/run_simple_analysis.py --data-source fbi --verbose
```