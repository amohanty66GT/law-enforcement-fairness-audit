"""
Ingestion Agent - Fetches data from FBI Wanted API and other sources.
Handles pagination, deduplication, and incremental updates.
"""

import pandas as pd
import requests
import time
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
import hashlib

from .base import BaseAgent, AgentMessage, AgentExecutionContext, ValidationResult, ProcessingError

class IngestionAgent(BaseAgent):
    """Agent responsible for data ingestion from external sources."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("ingestion_agent", config)
        self.base_url = self.config.get("fbi_api_url", "https://api.fbi.gov/wanted/v1/list")
        self.rate_limit_delay = self.config.get("rate_limit_delay", 1.0)
        self.max_pages = self.config.get("max_pages", 50)
        self.session = requests.Session()
        self.seen_records: Set[str] = set()
        
    def execute(self, context: AgentExecutionContext, input_data: Any) -> AgentMessage:
        """Execute data ingestion."""
        self.log_execution("starting_ingestion", {"source": "fbi_wanted_api"})
        
        try:
            # Check for incremental update parameters
            last_update = context.shared_data.get("last_ingestion_time")
            
            # Fetch data from FBI API
            raw_records = self._fetch_fbi_data(last_update)
            
            # Deduplicate records
            deduplicated_records = self._deduplicate_records(raw_records)
            
            # Version the records
            versioned_records = self._version_records(deduplicated_records)
            
            # Update context with ingestion metadata
            context.shared_data["last_ingestion_time"] = datetime.now()
            context.shared_data["ingestion_stats"] = {
                "total_fetched": len(raw_records),
                "after_deduplication": len(deduplicated_records),
                "new_records": len([r for r in versioned_records if r.get("is_new", False)])
            }
            
            self.log_execution("ingestion_completed", {
                "records_fetched": len(raw_records),
                "records_deduplicated": len(deduplicated_records)
            })
            
            return self.create_message(
                message_type="raw_data",
                data=versioned_records,
                metadata={
                    "source": "fbi_wanted_api",
                    "ingestion_time": datetime.now().isoformat(),
                    "record_count": len(versioned_records),
                    "deduplication_stats": {
                        "original_count": len(raw_records),
                        "deduplicated_count": len(deduplicated_records)
                    }
                }
            )
            
        except Exception as e:
            self.log_execution("ingestion_failed", {"error": str(e)})
            raise ProcessingError(self.agent_id, f"Ingestion failed: {str(e)}")
    
    def _fetch_fbi_data(self, last_update: Optional[datetime] = None) -> List[Dict]:
        """Fetch data from FBI Wanted API with pagination."""
        all_records = []
        page = 1
        
        while page <= self.max_pages:
            self.logger.info(f"Fetching page {page}")
            
            params = {
                'page': page,
                'pageSize': 50
            }
            
            try:
                response = self.session.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if 'items' not in data or not data['items']:
                    self.logger.info("No more data available")
                    break
                
                records = data['items']
                
                # Filter by last update time if provided
                if last_update:
                    records = self._filter_by_update_time(records, last_update)
                
                all_records.extend(records)
                
                # Check if we've reached the end
                if len(data['items']) < 50:
                    break
                
                page += 1
                time.sleep(self.rate_limit_delay)
                
            except requests.RequestException as e:
                self.logger.error(f"Error fetching page {page}: {e}")
                if page == 1:  # If first page fails, raise error
                    raise
                break  # Continue with what we have if later pages fail
        
        return all_records
    
    def _filter_by_update_time(self, records: List[Dict], last_update: datetime) -> List[Dict]:
        """Filter records by modification time for incremental updates."""
        filtered_records = []
        
        for record in records:
            modified_date_str = record.get('modified')
            if modified_date_str:
                try:
                    modified_date = pd.to_datetime(modified_date_str)
                    if modified_date > last_update:
                        filtered_records.append(record)
                except (ValueError, TypeError):
                    # Include record if we can't parse the date
                    filtered_records.append(record)
            else:
                # Include record if no modification date
                filtered_records.append(record)
        
        return filtered_records
    
    def _deduplicate_records(self, records: List[Dict]) -> List[Dict]:
        """Remove duplicate records based on UID and content hash."""
        deduplicated = []
        seen_uids = set()
        seen_hashes = set()
        
        for record in records:
            # Check UID-based deduplication
            uid = record.get('uid')
            if uid and uid in seen_uids:
                continue
            
            # Check content-based deduplication
            content_hash = self._compute_record_hash(record)
            if content_hash in seen_hashes:
                continue
            
            # Add to seen sets
            if uid:
                seen_uids.add(uid)
            seen_hashes.add(content_hash)
            
            # Add hash to record for tracking
            record['_content_hash'] = content_hash
            deduplicated.append(record)
        
        return deduplicated
    
    def _compute_record_hash(self, record: Dict) -> str:
        """Compute a hash of the record content for deduplication."""
        # Create a normalized representation for hashing
        key_fields = ['uid', 'title', 'description', 'publication']
        hash_content = []
        
        for field in key_fields:
            value = record.get(field, '')
            if isinstance(value, str):
                hash_content.append(value.strip().lower())
            else:
                hash_content.append(str(value))
        
        content_str = '|'.join(hash_content)
        return hashlib.md5(content_str.encode('utf-8')).hexdigest()
    
    def _version_records(self, records: List[Dict]) -> List[Dict]:
        """Add versioning information to records."""
        versioned_records = []
        current_time = datetime.now()
        
        for record in records:
            # Add versioning metadata
            record['_version'] = {
                'ingestion_time': current_time.isoformat(),
                'version_id': f"v_{int(current_time.timestamp())}",
                'is_new': record.get('_content_hash') not in self.seen_records
            }
            
            # Track this record
            content_hash = record.get('_content_hash')
            if content_hash:
                self.seen_records.add(content_hash)
            
            versioned_records.append(record)
        
        return versioned_records
    
    def validate_input(self, input_data: Any) -> ValidationResult:
        """Validate ingestion parameters."""
        errors = []
        warnings = []
        
        # For ingestion agent, input_data might contain configuration overrides
        if input_data and not isinstance(input_data, dict):
            errors.append("Input data must be a dictionary or None")
        
        if input_data:
            max_pages = input_data.get("max_pages")
            if max_pages and (not isinstance(max_pages, int) or max_pages <= 0):
                errors.append("max_pages must be a positive integer")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )