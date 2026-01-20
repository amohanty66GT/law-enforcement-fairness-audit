"""
Trend & Anomaly Agent - Analyzes longitudinal trends and detects anomalies.
Flags anomalous years or structural changes using rolling statistics.
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import warnings

from .base import BaseAgent, AgentMessage, AgentExecutionContext, TrendResult, ProcessingError, ValidationResult

class TrendAnomalyAgent(BaseAgent):
    """Agent responsible for trend analysis and anomaly detection."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("trend_anomaly_agent", config)
        self.min_time_periods = self.config.get("min_time_periods", 3)
        self.anomaly_threshold = self.config.get("anomaly_threshold", 2.0)  # Z-score threshold
        self.trend_significance_level = self.config.get("trend_significance_level", 0.05)
        self.rolling_window = self.config.get("rolling_window", 3)
        
    def execute(self, context: AgentExecutionContext, input_data: Any) -> AgentMessage:
        """Execute trend analysis and anomaly detection."""
        self.log_execution("starting_trend_analysis", {"record_count": len(input_data)})
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(input_data)
            
            # Prepare temporal data
            temporal_df = self._prepare_temporal_data(df)
            
            if temporal_df is None or len(temporal_df) < self.min_time_periods:
                return self.create_message(
                    message_type="trend_analysis_results",
                    data={"error": "Insufficient temporal data for trend analysis"},
                    metadata={"analysis_time": pd.Timestamp.now().isoformat()}
                )
            
            # Perform trend analyses
            trend_results = {}
            
            # Overall temporal trends
            trend_results["overall_trends"] = self._analyze_overall_trends(temporal_df)
            
            # Weapon category trends (if available)
            if self._has_weapon_data(df):
                trend_results["weapon_trends"] = self._analyze_weapon_trends(temporal_df)
            
            # Serious crime trends (if available)
            if self._has_severity_data(df):
                trend_results["severity_trends"] = self._analyze_severity_trends(temporal_df)
            
            # Geographic trends (if available)
            if self._has_geographic_data(df):
                trend_results["geographic_trends"] = self._analyze_geographic_trends(temporal_df)
            
            # Anomaly detection
            anomaly_results = self._detect_anomalies(temporal_df)
            
            # Change point detection
            change_points = self._detect_change_points(temporal_df)
            
            self.log_execution("trend_analysis_completed", {
                "trend_analyses": len(trend_results),
                "anomalies_detected": len(anomaly_results.get("anomalies", [])),
                "change_points_detected": len(change_points.get("change_points", []))
            })
            
            return self.create_message(
                message_type="trend_analysis_results",
                data={
                    "trend_results": trend_results,
                    "anomaly_results": anomaly_results,
                    "change_point_results": change_points,
                    "analysis_metadata": {
                        "time_periods_analyzed": len(temporal_df),
                        "date_range": {
                            "start": temporal_df.index.min().isoformat() if len(temporal_df) > 0 else None,
                            "end": temporal_df.index.max().isoformat() if len(temporal_df) > 0 else None
                        }
                    }
                },
                metadata={
                    "analysis_time": pd.Timestamp.now().isoformat(),
                    "agent_version": "1.0"
                }
            )
            
        except Exception as e:
            self.log_execution("trend_analysis_failed", {"error": str(e)})
            raise ProcessingError(self.agent_id, f"Trend analysis failed: {str(e)}")
    
    def _prepare_temporal_data(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Prepare data for temporal analysis."""
        # Find date column
        date_columns = ['publication_date', 'publication', 'modified_date', 'modified']
        date_col = None
        
        for col in date_columns:
            if col in df.columns:
                date_col = col
                break
        
        if date_col is None:
            return None
        
        # Convert to datetime and extract time periods
        df_temporal = df.copy()
        df_temporal['date_parsed'] = pd.to_datetime(df_temporal[date_col], errors='coerce')
        df_temporal = df_temporal.dropna(subset=['date_parsed'])
        
        if len(df_temporal) == 0:
            return None
        
        # Group by year-month for analysis
        df_temporal['year_month'] = df_temporal['date_parsed'].dt.to_period('M')
        
        # Aggregate data by time period
        temporal_agg = df_temporal.groupby('year_month').agg({
            'date_parsed': 'count',  # Total records
            'weapon_category': lambda x: x.value_counts().to_dict() if 'weapon_category' in df.columns else {},
            'severity_flag': lambda x: x.sum() if 'severity_flag' in df.columns else 0,
            'state': lambda x: x.value_counts().to_dict() if 'state' in df.columns else {}
        }).rename(columns={'date_parsed': 'total_records'})
        
        # Convert period index to datetime for easier manipulation
        temporal_agg.index = temporal_agg.index.to_timestamp()
        
        return temporal_agg
    
    def _has_weapon_data(self, df: pd.DataFrame) -> bool:
        """Check if weapon data is available."""
        return 'weapon_category' in df.columns
    
    def _has_severity_data(self, df: pd.DataFrame) -> bool:
        """Check if severity data is available."""
        return 'severity_flag' in df.columns
    
    def _has_geographic_data(self, df: pd.DataFrame) -> bool:
        """Check if geographic data is available."""
        return 'state' in df.columns
    
    def _analyze_overall_trends(self, temporal_df: pd.DataFrame) -> Dict:
        """Analyze overall temporal trends in record counts."""
        results = {"trend_type": "overall_records"}
        
        try:
            # Time series of total records
            time_series = temporal_df['total_records']
            
            # Linear trend analysis
            x = np.arange(len(time_series))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, time_series.values)
            
            # Determine trend direction and significance
            trend_direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
            is_significant = p_value < self.trend_significance_level
            
            # Calculate percentage change
            if len(time_series) >= 2:
                pct_change = ((time_series.iloc[-1] - time_series.iloc[0]) / time_series.iloc[0]) * 100
            else:
                pct_change = 0.0
            
            results.update({
                "slope": float(slope),
                "r_squared": float(r_value ** 2),
                "p_value": float(p_value),
                "trend_direction": trend_direction,
                "is_significant": is_significant,
                "percentage_change": float(pct_change),
                "time_series": time_series.to_dict(),
                "interpretation": self._interpret_trend(trend_direction, is_significant, pct_change, p_value)
            })
            
        except Exception as e:
            results["error"] = f"Overall trend analysis failed: {str(e)}"
        
        return results
    
    def _analyze_weapon_trends(self, temporal_df: pd.DataFrame) -> Dict:
        """Analyze trends in weapon categories over time."""
        results = {"trend_type": "weapon_categories"}
        weapon_trends = {}
        
        try:
            # Extract weapon category time series
            weapon_time_series = {}
            
            for idx, row in temporal_df.iterrows():
                weapon_counts = row['weapon_category']
                if isinstance(weapon_counts, dict):
                    for weapon, count in weapon_counts.items():
                        if weapon not in weapon_time_series:
                            weapon_time_series[weapon] = {}
                        weapon_time_series[weapon][idx] = count
            
            # Analyze trend for each weapon category
            for weapon, time_data in weapon_time_series.items():
                if len(time_data) >= self.min_time_periods:
                    weapon_trend = self._analyze_category_trend(time_data, weapon)
                    weapon_trends[weapon] = weapon_trend
            
            results["weapon_category_trends"] = weapon_trends
            
            # Find most significant trends
            significant_trends = [
                (weapon, trend) for weapon, trend in weapon_trends.items()
                if trend.get("is_significant", False)
            ]
            
            results["significant_weapon_trends"] = len(significant_trends)
            results["most_significant_trends"] = significant_trends[:5]  # Top 5
            
        except Exception as e:
            results["error"] = f"Weapon trend analysis failed: {str(e)}"
        
        return results
    
    def _analyze_severity_trends(self, temporal_df: pd.DataFrame) -> Dict:
        """Analyze trends in serious crime rates over time."""
        results = {"trend_type": "serious_crime_rates"}
        
        try:
            # Calculate serious crime rates over time
            serious_counts = temporal_df['severity_flag']
            total_counts = temporal_df['total_records']
            
            # Calculate rates (handle division by zero)
            rates = []
            valid_periods = []
            
            for i, (serious, total) in enumerate(zip(serious_counts, total_counts)):
                if total > 0:
                    rate = serious / total
                    rates.append(rate)
                    valid_periods.append(i)
            
            if len(rates) >= self.min_time_periods:
                # Trend analysis on rates
                x = np.array(valid_periods)
                y = np.array(rates)
                
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                
                trend_direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
                is_significant = p_value < self.trend_significance_level
                
                # Calculate percentage point change
                if len(rates) >= 2:
                    pp_change = (rates[-1] - rates[0]) * 100  # Percentage points
                else:
                    pp_change = 0.0
                
                results.update({
                    "slope": float(slope),
                    "r_squared": float(r_value ** 2),
                    "p_value": float(p_value),
                    "trend_direction": trend_direction,
                    "is_significant": is_significant,
                    "percentage_point_change": float(pp_change),
                    "serious_crime_rates": dict(zip(temporal_df.index[valid_periods], rates)),
                    "interpretation": self._interpret_rate_trend(trend_direction, is_significant, pp_change, p_value)
                })
            else:
                results["error"] = "Insufficient data for serious crime trend analysis"
                
        except Exception as e:
            results["error"] = f"Severity trend analysis failed: {str(e)}"
        
        return results
    
    def _analyze_geographic_trends(self, temporal_df: pd.DataFrame) -> Dict:
        """Analyze geographic distribution trends over time."""
        results = {"trend_type": "geographic_distribution"}
        
        try:
            # Extract top states and analyze their trends
            all_states = set()
            for row in temporal_df['state']:
                if isinstance(row, dict):
                    all_states.update(row.keys())
            
            # Focus on top states by total count
            state_totals = {}
            for state in all_states:
                total = 0
                for row in temporal_df['state']:
                    if isinstance(row, dict):
                        total += row.get(state, 0)
                state_totals[state] = total
            
            # Analyze trends for top 5 states
            top_states = sorted(state_totals.items(), key=lambda x: x[1], reverse=True)[:5]
            
            geographic_trends = {}
            for state, _ in top_states:
                state_time_series = {}
                for idx, row in temporal_df.iterrows():
                    state_counts = row['state']
                    if isinstance(state_counts, dict):
                        state_time_series[idx] = state_counts.get(state, 0)
                
                if len(state_time_series) >= self.min_time_periods:
                    state_trend = self._analyze_category_trend(state_time_series, state)
                    geographic_trends[state] = state_trend
            
            results["geographic_trends"] = geographic_trends
            
        except Exception as e:
            results["error"] = f"Geographic trend analysis failed: {str(e)}"
        
        return results
    
    def _analyze_category_trend(self, time_data: Dict, category_name: str) -> Dict:
        """Analyze trend for a specific category."""
        # Convert to time series
        dates = sorted(time_data.keys())
        values = [time_data[date] for date in dates]
        
        if len(values) < self.min_time_periods:
            return {"error": "Insufficient data points"}
        
        # Linear regression
        x = np.arange(len(values))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
        
        trend_direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
        is_significant = p_value < self.trend_significance_level
        
        # Calculate percentage change
        if values[0] != 0:
            pct_change = ((values[-1] - values[0]) / values[0]) * 100
        else:
            pct_change = float('inf') if values[-1] > 0 else 0.0
        
        return {
            "category": category_name,
            "slope": float(slope),
            "r_squared": float(r_value ** 2),
            "p_value": float(p_value),
            "trend_direction": trend_direction,
            "is_significant": is_significant,
            "percentage_change": float(pct_change) if not np.isinf(pct_change) else "infinite",
            "time_series": dict(zip([d.isoformat() for d in dates], values))
        }
    
    def _detect_anomalies(self, temporal_df: pd.DataFrame) -> Dict:
        """Detect anomalous time periods using statistical methods."""
        anomalies = []
        
        try:
            # Analyze total records for anomalies
            time_series = temporal_df['total_records']
            
            if len(time_series) >= 3:
                # Calculate rolling statistics
                rolling_mean = time_series.rolling(window=self.rolling_window, center=True).mean()
                rolling_std = time_series.rolling(window=self.rolling_window, center=True).std()
                
                # Calculate z-scores
                z_scores = (time_series - rolling_mean) / rolling_std
                
                # Identify anomalies
                for date, z_score in z_scores.items():
                    if abs(z_score) > self.anomaly_threshold:
                        anomaly_type = "high" if z_score > 0 else "low"
                        anomalies.append({
                            "date": date.isoformat(),
                            "value": float(time_series[date]),
                            "z_score": float(z_score),
                            "anomaly_type": anomaly_type,
                            "severity": "extreme" if abs(z_score) > 3 else "moderate"
                        })
            
        except Exception as e:
            return {"error": f"Anomaly detection failed: {str(e)}"}
        
        return {
            "anomalies": anomalies,
            "anomaly_count": len(anomalies),
            "threshold_used": self.anomaly_threshold
        }
    
    def _detect_change_points(self, temporal_df: pd.DataFrame) -> Dict:
        """Detect structural change points in the time series."""
        change_points = []
        
        try:
            time_series = temporal_df['total_records'].values
            
            if len(time_series) >= 6:  # Need minimum data for change point detection
                # Simple change point detection using variance
                for i in range(2, len(time_series) - 2):
                    # Split series at point i
                    before = time_series[:i]
                    after = time_series[i:]
                    
                    # Calculate means and test for significant difference
                    if len(before) >= 2 and len(after) >= 2:
                        t_stat, p_value = stats.ttest_ind(before, after)
                        
                        if p_value < 0.05:  # Significant change
                            change_points.append({
                                "date": temporal_df.index[i].isoformat(),
                                "position": i,
                                "t_statistic": float(t_stat),
                                "p_value": float(p_value),
                                "mean_before": float(np.mean(before)),
                                "mean_after": float(np.mean(after)),
                                "change_magnitude": float(np.mean(after) - np.mean(before))
                            })
            
        except Exception as e:
            return {"error": f"Change point detection failed: {str(e)}"}
        
        return {
            "change_points": change_points,
            "change_point_count": len(change_points)
        }
    
    def _interpret_trend(self, direction: str, significant: bool, pct_change: float, p_value: float) -> str:
        """Interpret overall trend results."""
        if significant:
            return (f"Significant {direction} trend detected (p={p_value:.4f}). "
                   f"Overall change: {pct_change:+.1f}%.")
        else:
            return f"No significant trend detected (p={p_value:.4f}). Data appears stable."
    
    def _interpret_rate_trend(self, direction: str, significant: bool, pp_change: float, p_value: float) -> str:
        """Interpret rate trend results."""
        if significant:
            return (f"Significant {direction} trend in serious crime rate (p={p_value:.4f}). "
                   f"Change: {pp_change:+.1f} percentage points.")
        else:
            return f"No significant trend in serious crime rate (p={p_value:.4f})."
    
    def validate_input(self, input_data: Any) -> ValidationResult:
        """Validate input data for trend analysis."""
        errors = []
        warnings = []
        
        if not isinstance(input_data, list):
            errors.append("Input data must be a list of records")
        elif len(input_data) == 0:
            errors.append("Input data cannot be empty")
        else:
            # Check for temporal data
            df = pd.DataFrame(input_data)
            date_columns = ['publication_date', 'publication', 'modified_date', 'modified']
            has_date_col = any(col in df.columns for col in date_columns)
            
            if not has_date_col:
                errors.append("No temporal data found for trend analysis")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )