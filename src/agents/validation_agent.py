"""
Validation & Drift Agent - Validates schema consistency and monitors data drift.
Tracks missing rates and flags distribution shifts over time.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from scipy import stats

from .base import BaseAgent, AgentMessage, AgentExecutionContext, ValidationResult, ValidationError

class ValidationDriftAgent(BaseAgent):
    """Agent responsible for data validation and drift detection."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("validation_drift_agent", config)
        self.required_fields = self.config.get("required_fields", [
            'uid', 'title', 'description', 'publication'
        ])
        self.drift_threshold = self.config.get("drift_threshold", 0.1)  # 10% change threshold
        self.missing_rate_threshold = self.config.get("missing_rate_threshold", 0.5)  # 50% missing
        self.historical_data: List[Dict] = []
        
    def execute(self, context: AgentExecutionContext, input_data: Any) -> AgentMessage:
        """Execute validation and drift detection."""
        self.log_execution("starting_validation", {"record_count": len(input_data)})
        
        try:
            # Convert to DataFrame for analysis
            df = pd.DataFrame(input_data)
            
            # Schema validation
            schema_validation = self._validate_schema(df)
            
            # Data quality validation
            quality_validation = self._validate_data_quality(df)
            
            # Drift detection
            drift_analysis = self._detect_drift(df, context)
            
            # Missing data analysis
            missing_analysis = self._analyze_missing_data(df)
            
            # Compile validation report
            validation_report = {
                "schema_validation": schema_validation,
                "quality_validation": quality_validation,
                "drift_analysis": drift_analysis,
                "missing_analysis": missing_analysis,
                "overall_status": self._determine_overall_status(
                    schema_validation, quality_validation, drift_analysis
                )
            }
            
            # Store current data for future drift detection
            self._update_historical_data(df)
            
            self.log_execution("validation_completed", {
                "overall_status": validation_report["overall_status"],
                "schema_errors": len(schema_validation.get("errors", [])),
                "drift_detected": drift_analysis.get("drift_detected", False)
            })
            
            return self.create_message(
                message_type="validation_report",
                data=validation_report,
                metadata={
                    "validation_time": datetime.now().isoformat(),
                    "record_count": len(df),
                    "validation_agent_version": "1.0"
                }
            )
            
        except Exception as e:
            self.log_execution("validation_failed", {"error": str(e)})
            raise ValidationError(self.agent_id, f"Validation failed: {str(e)}")
    
    def _validate_schema(self, df: pd.DataFrame) -> Dict:
        """Validate schema consistency and required fields."""
        errors = []
        warnings = []
        
        # Check required fields
        missing_fields = [field for field in self.required_fields if field not in df.columns]
        if missing_fields:
            errors.append(f"Missing required fields: {missing_fields}")
        
        # Check data types
        type_issues = []
        for column in df.columns:
            if column in ['publication', 'modified']:
                # Should be datetime-parseable
                try:
                    pd.to_datetime(df[column], errors='coerce')
                except Exception:
                    type_issues.append(f"Column {column} contains non-datetime values")
        
        if type_issues:
            warnings.extend(type_issues)
        
        # Check for completely empty columns
        empty_columns = [col for col in df.columns if df[col].isna().all()]
        if empty_columns:
            warnings.append(f"Completely empty columns: {empty_columns}")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "columns_found": list(df.columns),
            "required_fields_status": {
                field: field in df.columns for field in self.required_fields
            }
        }
    
    def _validate_data_quality(self, df: pd.DataFrame) -> Dict:
        """Validate data quality metrics."""
        quality_issues = []
        warnings = []
        
        # Check for duplicate UIDs
        if 'uid' in df.columns:
            duplicate_uids = df['uid'].duplicated().sum()
            if duplicate_uids > 0:
                quality_issues.append(f"Found {duplicate_uids} duplicate UIDs")
        
        # Check for extremely short or long text fields
        text_fields = ['title', 'description']
        for field in text_fields:
            if field in df.columns:
                text_lengths = df[field].astype(str).str.len()
                very_short = (text_lengths < 5).sum()
                very_long = (text_lengths > 10000).sum()
                
                if very_short > len(df) * 0.1:  # More than 10% very short
                    warnings.append(f"Many very short {field} values: {very_short}")
                
                if very_long > 0:
                    warnings.append(f"Very long {field} values: {very_long}")
        
        # Check for suspicious patterns
        if 'title' in df.columns:
            # Check for too many identical titles
            title_counts = df['title'].value_counts()
            max_identical = title_counts.iloc[0] if len(title_counts) > 0 else 0
            if max_identical > len(df) * 0.2:  # More than 20% identical
                warnings.append(f"High number of identical titles: {max_identical}")
        
        return {
            "is_valid": len(quality_issues) == 0,
            "errors": quality_issues,
            "warnings": warnings,
            "record_count": len(df),
            "duplicate_rate": duplicate_uids / len(df) if 'uid' in df.columns else 0
        }
    
    def _detect_drift(self, df: pd.DataFrame, context: AgentExecutionContext) -> Dict:
        """Detect distribution drift compared to historical data."""
        drift_results = {
            "drift_detected": False,
            "drift_details": [],
            "comparison_available": False
        }
        
        if not self.historical_data:
            drift_results["message"] = "No historical data available for drift detection"
            return drift_results
        
        # Get the most recent historical snapshot
        historical_df = pd.DataFrame(self.historical_data[-1]["data"])
        drift_results["comparison_available"] = True
        
        # Compare key distributions
        drift_details = []
        
        # Check publication date distribution
        if 'publication' in df.columns and 'publication' in historical_df.columns:
            current_dates = pd.to_datetime(df['publication'], errors='coerce')
            historical_dates = pd.to_datetime(historical_df['publication'], errors='coerce')
            
            # Compare year distributions
            current_years = current_dates.dt.year.value_counts(normalize=True)
            historical_years = historical_dates.dt.year.value_counts(normalize=True)
            
            # Calculate distribution difference
            common_years = set(current_years.index) & set(historical_years.index)
            if common_years:
                year_drift = sum(abs(current_years.get(year, 0) - historical_years.get(year, 0)) 
                               for year in common_years)
                
                if year_drift > self.drift_threshold:
                    drift_details.append({
                        "field": "publication_year",
                        "drift_magnitude": year_drift,
                        "description": f"Publication year distribution changed by {year_drift:.3f}"
                    })
        
        # Check missing data rates
        current_missing = df.isnull().mean()
        historical_missing = historical_df.isnull().mean()
        
        for column in current_missing.index:
            if column in historical_missing.index:
                missing_change = abs(current_missing[column] - historical_missing[column])
                if missing_change > self.drift_threshold:
                    drift_details.append({
                        "field": f"{column}_missing_rate",
                        "drift_magnitude": missing_change,
                        "description": f"Missing rate for {column} changed by {missing_change:.3f}"
                    })
        
        drift_results["drift_detected"] = len(drift_details) > 0
        drift_results["drift_details"] = drift_details
        
        return drift_results
    
    def _analyze_missing_data(self, df: pd.DataFrame) -> Dict:
        """Analyze missing data patterns."""
        missing_analysis = {}
        
        # Overall missing rates
        missing_rates = df.isnull().mean().to_dict()
        
        # Flag fields with high missing rates
        high_missing_fields = [
            field for field, rate in missing_rates.items() 
            if rate > self.missing_rate_threshold
        ]
        
        # Weapon field specific analysis (if present)
        weapon_fields = [col for col in df.columns if 'weapon' in col.lower()]
        weapon_missing_analysis = {}
        
        for field in weapon_fields:
            if field in df.columns:
                missing_rate = df[field].isnull().mean()
                weapon_missing_analysis[field] = {
                    "missing_rate": missing_rate,
                    "missing_count": df[field].isnull().sum(),
                    "status": "high" if missing_rate > self.missing_rate_threshold else "acceptable"
                }
        
        missing_analysis = {
            "overall_missing_rates": missing_rates,
            "high_missing_fields": high_missing_fields,
            "weapon_fields_analysis": weapon_missing_analysis,
            "total_complete_records": df.dropna().shape[0],
            "completeness_rate": df.dropna().shape[0] / len(df) if len(df) > 0 else 0
        }
        
        return missing_analysis
    
    def _determine_overall_status(self, schema_val: Dict, quality_val: Dict, drift_analysis: Dict) -> str:
        """Determine overall validation status."""
        if not schema_val.get("is_valid", False):
            return "FAILED"
        
        if not quality_val.get("is_valid", False):
            return "FAILED"
        
        if drift_analysis.get("drift_detected", False):
            return "WARNING"
        
        if (schema_val.get("warnings", []) or 
            quality_val.get("warnings", [])):
            return "WARNING"
        
        return "PASSED"
    
    def _update_historical_data(self, df: pd.DataFrame):
        """Update historical data for drift detection."""
        # Keep only recent snapshots (last 10)
        max_snapshots = self.config.get("max_historical_snapshots", 10)
        
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "data": df.to_dict('records'),
            "summary_stats": {
                "record_count": len(df),
                "missing_rates": df.isnull().mean().to_dict()
            }
        }
        
        self.historical_data.append(snapshot)
        
        # Keep only recent snapshots
        if len(self.historical_data) > max_snapshots:
            self.historical_data = self.historical_data[-max_snapshots:]
    
    def validate_input(self, input_data: Any) -> ValidationResult:
        """Validate input data format."""
        errors = []
        
        if not isinstance(input_data, list):
            errors.append("Input data must be a list of records")
        elif len(input_data) == 0:
            errors.append("Input data cannot be empty")
        elif not all(isinstance(record, dict) for record in input_data):
            errors.append("All records must be dictionaries")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )