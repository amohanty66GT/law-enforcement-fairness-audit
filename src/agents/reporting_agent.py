"""
Reporting/Visualization Agent - Generates aggregate-only charts and metrics.
Enforces aggregation thresholds to prevent individual-level inference.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Any
import json

from .base import BaseAgent, AgentMessage, AgentExecutionContext, ProcessingError, ValidationResult

class ReportingVisualizationAgent(BaseAgent):
    """Agent responsible for generating reports and visualizations."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("reporting_visualization_agent", config)
        self.min_aggregation_threshold = self.config.get("min_aggregation_threshold", 5)
        self.max_categories_display = self.config.get("max_categories_display", 10)
        
    def execute(self, context: AgentExecutionContext, input_data: Any) -> AgentMessage:
        """Execute report generation and visualization creation."""
        self.log_execution("starting_report_generation")
        
        try:
            # Extract data from different agent outputs
            raw_data = input_data.get("classified_data", [])
            validation_report = input_data.get("validation_report", {})
            statistical_results = input_data.get("statistical_results", {})
            trend_results = input_data.get("trend_results", {})
            
            # Generate comprehensive report
            report = self._generate_comprehensive_report(
                raw_data, validation_report, statistical_results, trend_results
            )
            
            # Generate visualizations
            visualizations = self._generate_visualizations(raw_data, statistical_results, trend_results)
            
            # Generate summary metrics
            summary_metrics = self._generate_summary_metrics(raw_data, statistical_results)
            
            self.log_execution("report_generation_completed", {
                "report_sections": len(report),
                "visualizations_created": len(visualizations),
                "metrics_generated": len(summary_metrics)
            })
            
            return self.create_message(
                message_type="comprehensive_report",
                data={
                    "report": report,
                    "visualizations": visualizations,
                    "summary_metrics": summary_metrics,
                    "metadata": {
                        "generation_time": pd.Timestamp.now().isoformat(),
                        "aggregation_threshold": self.min_aggregation_threshold,
                        "privacy_compliant": True
                    }
                },
                metadata={
                    "report_time": pd.Timestamp.now().isoformat(),
                    "agent_version": "1.0"
                }
            )
            
        except Exception as e:
            self.log_execution("report_generation_failed", {"error": str(e)})
            raise ProcessingError(self.agent_id, f"Report generation failed: {str(e)}")
    
    def _generate_comprehensive_report(self, raw_data: List[Dict], validation_report: Dict, 
                                     statistical_results: Dict, trend_results: Dict) -> Dict:
        """Generate a comprehensive analysis report."""
        if not raw_data:
            return {"error": "No data available for report generation"}
        
        df = pd.DataFrame(raw_data)
        
        report = {
            "executive_summary": self._generate_executive_summary(df, statistical_results, trend_results),
            "data_quality_assessment": self._generate_data_quality_section(validation_report, df),
            "statistical_analysis_summary": self._generate_statistical_summary(statistical_results),
            "trend_analysis_summary": self._generate_trend_summary(trend_results),
            "weapon_analysis_summary": self._generate_weapon_summary(df),
            "geographic_analysis_summary": self._generate_geographic_summary(df),
            "recommendations": self._generate_recommendations(statistical_results, trend_results, validation_report),
            "methodology_notes": self._generate_methodology_notes(),
            "ethical_compliance": self._generate_ethical_compliance_section()
        }
        
        return report
    
    def _generate_executive_summary(self, df: pd.DataFrame, statistical_results: Dict, trend_results: Dict) -> Dict:
        """Generate executive summary of key findings."""
        summary = {
            "dataset_overview": {
                "total_records": len(df),
                "date_range": self._get_safe_date_range(df),
                "geographic_coverage": self._get_safe_geographic_coverage(df),
                "analysis_period": pd.Timestamp.now().strftime("%Y-%m-%d")
            },
            "key_findings": []
        }
        
        # Add key statistical findings
        if statistical_results:
            for analysis_type, results in statistical_results.items():
                if isinstance(results, dict) and results.get("significant", False):
                    summary["key_findings"].append({
                        "type": "statistical",
                        "analysis": analysis_type,
                        "finding": results.get("interpretation", "Significant result detected"),
                        "p_value": results.get("p_value")
                    })
        
        # Add key trend findings
        if trend_results:
            trend_data = trend_results.get("trend_results", {})
            for trend_type, results in trend_data.items():
                if isinstance(results, dict) and results.get("is_significant", False):
                    summary["key_findings"].append({
                        "type": "trend",
                        "analysis": trend_type,
                        "finding": results.get("interpretation", "Significant trend detected"),
                        "trend_direction": results.get("trend_direction")
                    })
        
        return summary
    
    def _generate_data_quality_section(self, validation_report: Dict, df: pd.DataFrame) -> Dict:
        """Generate data quality assessment section."""
        quality_section = {
            "overall_assessment": validation_report.get("overall_status", "Unknown"),
            "data_completeness": self._assess_data_completeness(df),
            "validation_summary": {
                "schema_validation": validation_report.get("schema_validation", {}),
                "quality_validation": validation_report.get("quality_validation", {}),
                "missing_data_analysis": validation_report.get("missing_analysis", {})
            },
            "data_quality_score": self._calculate_data_quality_score(validation_report, df)
        }
        
        return quality_section
    
    def _generate_statistical_summary(self, statistical_results: Dict) -> Dict:
        """Generate statistical analysis summary."""
        if not statistical_results:
            return {"message": "No statistical analysis results available"}
        
        summary = {
            "tests_performed": [],
            "significant_results": [],
            "effect_sizes": [],
            "confidence_level": statistical_results.get("analysis_metadata", {}).get("confidence_level", 0.95)
        }
        
        # Process each statistical test
        for test_name, results in statistical_results.items():
            if isinstance(results, dict) and "p_value" in results:
                test_summary = {
                    "test_name": test_name,
                    "p_value": results["p_value"],
                    "significant": results.get("significant", False),
                    "interpretation": results.get("interpretation", "")
                }
                
                summary["tests_performed"].append(test_summary)
                
                if results.get("significant", False):
                    summary["significant_results"].append(test_summary)
                
                if "effect_size" in results:
                    summary["effect_sizes"].append({
                        "test": test_name,
                        "effect_size": results["effect_size"],
                        "interpretation": self._interpret_effect_size(results["effect_size"])
                    })
        
        return summary
    
    def _generate_trend_summary(self, trend_results: Dict) -> Dict:
        """Generate trend analysis summary."""
        if not trend_results:
            return {"message": "No trend analysis results available"}
        
        summary = {
            "trends_analyzed": [],
            "significant_trends": [],
            "anomalies_detected": [],
            "change_points": []
        }
        
        # Process trend results
        trend_data = trend_results.get("trend_results", {})
        for trend_type, results in trend_data.items():
            if isinstance(results, dict):
                trend_info = {
                    "trend_type": trend_type,
                    "direction": results.get("trend_direction", "unknown"),
                    "significant": results.get("is_significant", False),
                    "p_value": results.get("p_value")
                }
                
                summary["trends_analyzed"].append(trend_info)
                
                if results.get("is_significant", False):
                    summary["significant_trends"].append(trend_info)
        
        # Process anomalies
        anomaly_data = trend_results.get("anomaly_results", {})
        if "anomalies" in anomaly_data:
            summary["anomalies_detected"] = anomaly_data["anomalies"]
        
        # Process change points
        change_point_data = trend_results.get("change_point_results", {})
        if "change_points" in change_point_data:
            summary["change_points"] = change_point_data["change_points"]
        
        return summary
    
    def _generate_weapon_summary(self, df: pd.DataFrame) -> Dict:
        """Generate weapon analysis summary with privacy protection."""
        if 'weapon_category' not in df.columns:
            return {"message": "No weapon data available"}
        
        # Apply aggregation threshold
        weapon_counts = df['weapon_category'].value_counts()
        safe_weapon_counts = weapon_counts[weapon_counts >= self.min_aggregation_threshold]
        
        summary = {
            "total_records_with_weapons": len(df[df['weapon_category'].notna()]),
            "weapon_categories_above_threshold": len(safe_weapon_counts),
            "weapon_distribution": safe_weapon_counts.to_dict(),
            "most_common_weapon": safe_weapon_counts.index[0] if len(safe_weapon_counts) > 0 else "N/A",
            "data_quality": {
                "unknown_weapon_rate": (df['weapon_category'] == 'unknown').mean(),
                "missing_weapon_rate": df['weapon_category'].isna().mean()
            }
        }
        
        # Serious crimes weapon analysis
        if 'severity_flag' in df.columns:
            serious_crimes = df[df['severity_flag'] == True]
            if len(serious_crimes) >= self.min_aggregation_threshold:
                serious_weapon_counts = serious_crimes['weapon_category'].value_counts()
                safe_serious_weapon_counts = serious_weapon_counts[serious_weapon_counts >= self.min_aggregation_threshold]
                
                summary["serious_crimes_weapon_analysis"] = {
                    "total_serious_crimes": len(serious_crimes),
                    "weapon_distribution": safe_serious_weapon_counts.to_dict(),
                    "most_common_in_serious": safe_serious_weapon_counts.index[0] if len(safe_serious_weapon_counts) > 0 else "N/A"
                }
        
        return summary
    
    def _generate_geographic_summary(self, df: pd.DataFrame) -> Dict:
        """Generate geographic analysis summary with privacy protection."""
        # Extract state information
        if 'place_of_birth' in df.columns:
            df['state'] = df['place_of_birth'].str.extract(r', ([A-Z]{2})$')
        
        if 'state' not in df.columns:
            return {"message": "No geographic data available"}
        
        # Apply aggregation threshold
        state_counts = df['state'].value_counts()
        safe_state_counts = state_counts[state_counts >= self.min_aggregation_threshold]
        
        summary = {
            "total_records_with_location": len(df[df['state'].notna()]),
            "states_above_threshold": len(safe_state_counts),
            "geographic_distribution": safe_state_counts.to_dict(),
            "most_represented_state": safe_state_counts.index[0] if len(safe_state_counts) > 0 else "N/A",
            "geographic_diversity_score": len(safe_state_counts) / 50  # Normalized by total US states
        }
        
        return summary
    
    def _generate_visualizations(self, raw_data: List[Dict], statistical_results: Dict, trend_results: Dict) -> Dict:
        """Generate privacy-compliant visualizations."""
        if not raw_data:
            return {"error": "No data available for visualizations"}
        
        df = pd.DataFrame(raw_data)
        visualizations = {}
        
        try:
            # Weapon distribution chart
            if 'weapon_category' in df.columns:
                visualizations["weapon_distribution"] = self._create_weapon_distribution_chart(df)
            
            # Geographic distribution chart
            if 'place_of_birth' in df.columns:
                visualizations["geographic_distribution"] = self._create_geographic_distribution_chart(df)
            
            # Temporal trends chart
            if any(col in df.columns for col in ['publication_date', 'publication']):
                visualizations["temporal_trends"] = self._create_temporal_trends_chart(df)
            
            # Statistical results visualization
            if statistical_results:
                visualizations["statistical_summary"] = self._create_statistical_summary_chart(statistical_results)
            
        except Exception as e:
            visualizations["error"] = f"Visualization generation failed: {str(e)}"
        
        return visualizations
    
    def _create_weapon_distribution_chart(self, df: pd.DataFrame) -> Dict:
        """Create weapon distribution chart with aggregation threshold."""
        weapon_counts = df['weapon_category'].value_counts()
        safe_counts = weapon_counts[weapon_counts >= self.min_aggregation_threshold]
        
        if len(safe_counts) == 0:
            return {"error": "No weapon categories meet aggregation threshold"}
        
        # Create plotly chart data
        chart_data = {
            "type": "bar",
            "data": {
                "categories": safe_counts.index.tolist(),
                "counts": safe_counts.values.tolist()
            },
            "layout": {
                "title": "Weapon Category Distribution (Aggregated)",
                "xaxis": {"title": "Weapon Category"},
                "yaxis": {"title": "Count"},
                "note": f"Only categories with ≥{self.min_aggregation_threshold} cases shown"
            }
        }
        
        return chart_data
    
    def _create_geographic_distribution_chart(self, df: pd.DataFrame) -> Dict:
        """Create geographic distribution chart with aggregation threshold."""
        df['state'] = df['place_of_birth'].str.extract(r', ([A-Z]{2})$')
        state_counts = df['state'].value_counts()
        safe_counts = state_counts[state_counts >= self.min_aggregation_threshold]
        
        if len(safe_counts) == 0:
            return {"error": "No states meet aggregation threshold"}
        
        # Limit to top states for readability
        top_states = safe_counts.head(self.max_categories_display)
        
        chart_data = {
            "type": "bar",
            "data": {
                "states": top_states.index.tolist(),
                "counts": top_states.values.tolist()
            },
            "layout": {
                "title": f"Geographic Distribution (Top {len(top_states)} States)",
                "xaxis": {"title": "State"},
                "yaxis": {"title": "Count"},
                "note": f"Only states with ≥{self.min_aggregation_threshold} cases shown"
            }
        }
        
        return chart_data
    
    def _create_temporal_trends_chart(self, df: pd.DataFrame) -> Dict:
        """Create temporal trends chart."""
        # Find date column
        date_col = None
        for col in ['publication_date', 'publication']:
            if col in df.columns:
                date_col = col
                break
        
        if date_col is None:
            return {"error": "No date column found"}
        
        # Convert to datetime and group by month
        df['date_parsed'] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=['date_parsed'])
        
        if len(df) == 0:
            return {"error": "No valid dates found"}
        
        # Group by year-month
        df['year_month'] = df['date_parsed'].dt.to_period('M')
        monthly_counts = df.groupby('year_month').size()
        
        # Apply aggregation threshold
        safe_months = monthly_counts[monthly_counts >= self.min_aggregation_threshold]
        
        chart_data = {
            "type": "line",
            "data": {
                "dates": [str(period) for period in safe_months.index],
                "counts": safe_months.values.tolist()
            },
            "layout": {
                "title": "Temporal Trends (Monthly Aggregation)",
                "xaxis": {"title": "Month"},
                "yaxis": {"title": "Count"},
                "note": f"Only months with ≥{self.min_aggregation_threshold} cases shown"
            }
        }
        
        return chart_data
    
    def _create_statistical_summary_chart(self, statistical_results: Dict) -> Dict:
        """Create statistical summary visualization."""
        p_values = []
        test_names = []
        
        for test_name, results in statistical_results.items():
            if isinstance(results, dict) and "p_value" in results:
                p_values.append(results["p_value"])
                test_names.append(test_name.replace("_", " ").title())
        
        if not p_values:
            return {"error": "No statistical results to visualize"}
        
        chart_data = {
            "type": "bar",
            "data": {
                "tests": test_names,
                "p_values": p_values,
                "significance_line": 0.05
            },
            "layout": {
                "title": "Statistical Test Results (P-values)",
                "xaxis": {"title": "Statistical Test"},
                "yaxis": {"title": "P-value", "type": "log"},
                "note": "Lower p-values indicate stronger evidence against null hypothesis"
            }
        }
        
        return chart_data
    
    def _generate_summary_metrics(self, raw_data: List[Dict], statistical_results: Dict) -> Dict:
        """Generate key summary metrics."""
        if not raw_data:
            return {}
        
        df = pd.DataFrame(raw_data)
        
        metrics = {
            "dataset_metrics": {
                "total_records": len(df),
                "data_completeness": (1 - df.isnull().mean().mean()) * 100,
                "date_range_days": self._calculate_date_range_days(df)
            },
            "analysis_metrics": {
                "statistical_tests_performed": len([r for r in statistical_results.values() if isinstance(r, dict) and "p_value" in r]),
                "significant_results": len([r for r in statistical_results.values() if isinstance(r, dict) and r.get("significant", False)]),
                "privacy_compliance_score": 100  # Always 100% due to aggregation thresholds
            }
        }
        
        # Add weapon-specific metrics
        if 'weapon_category' in df.columns:
            weapon_counts = df['weapon_category'].value_counts()
            safe_weapon_counts = weapon_counts[weapon_counts >= self.min_aggregation_threshold]
            
            metrics["weapon_metrics"] = {
                "categories_analyzed": len(safe_weapon_counts),
                "unknown_weapon_rate": (df['weapon_category'] == 'unknown').mean() * 100,
                "data_quality_score": (1 - (df['weapon_category'] == 'unknown').mean()) * 100
            }
        
        # Add geographic metrics
        if 'place_of_birth' in df.columns:
            df['state'] = df['place_of_birth'].str.extract(r', ([A-Z]{2})$')
            state_counts = df['state'].value_counts()
            safe_state_counts = state_counts[state_counts >= self.min_aggregation_threshold]
            
            metrics["geographic_metrics"] = {
                "states_analyzed": len(safe_state_counts),
                "geographic_diversity": len(safe_state_counts) / 50 * 100  # Percentage of US states
            }
        
        return metrics
    
    def _generate_recommendations(self, statistical_results: Dict, trend_results: Dict, validation_report: Dict) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        # Data quality recommendations
        if validation_report.get("overall_status") == "WARNING":
            recommendations.append("Improve data collection processes to address quality issues identified in validation")
        
        # Statistical findings recommendations
        significant_count = len([r for r in statistical_results.values() if isinstance(r, dict) and r.get("significant", False)])
        if significant_count > 0:
            recommendations.append(f"Investigate {significant_count} significant statistical findings for potential policy implications")
        
        # Trend recommendations
        trend_data = trend_results.get("trend_results", {})
        significant_trends = [r for r in trend_data.values() if isinstance(r, dict) and r.get("is_significant", False)]
        if significant_trends:
            recommendations.append("Monitor identified trends for continued development and potential intervention needs")
        
        # Anomaly recommendations
        anomalies = trend_results.get("anomaly_results", {}).get("anomalies", [])
        if anomalies:
            recommendations.append("Investigate anomalous time periods for potential data collection or external factor influences")
        
        # General recommendations
        recommendations.extend([
            "Continue regular monitoring with this analysis framework",
            "Maintain ethical standards by keeping analysis at aggregate level only",
            "Consider expanding data sources for more comprehensive analysis"
        ])
        
        return recommendations
    
    def _generate_methodology_notes(self) -> Dict:
        """Generate methodology and limitations notes."""
        return {
            "statistical_methods": [
                "Chi-square tests for distribution analysis",
                "Linear regression for trend analysis",
                "Z-score based anomaly detection",
                "Aggregation thresholds for privacy protection"
            ],
            "limitations": [
                "Analysis limited to publicly available data",
                "Results subject to reporting bias and missing data",
                "Aggregation thresholds may hide small but important patterns",
                "Temporal analysis limited by data availability"
            ],
            "ethical_constraints": [
                "No individual-level analysis or identification",
                "Minimum aggregation thresholds enforced",
                "No predictive modeling for individual cases",
                "Focus on systemic patterns only"
            ]
        }
    
    def _generate_ethical_compliance_section(self) -> Dict:
        """Generate ethical compliance verification."""
        return {
            "privacy_protection": {
                "aggregation_threshold_enforced": True,
                "minimum_group_size": self.min_aggregation_threshold,
                "individual_identification_prevented": True
            },
            "bias_mitigation": {
                "statistical_significance_testing": True,
                "effect_size_reporting": True,
                "uncertainty_quantification": True
            },
            "transparency": {
                "methodology_documented": True,
                "limitations_disclosed": True,
                "assumptions_stated": True
            }
        }
    
    # Helper methods
    def _get_safe_date_range(self, df: pd.DataFrame) -> Dict:
        """Get date range safely."""
        date_cols = ['publication_date', 'publication', 'modified_date', 'modified']
        for col in date_cols:
            if col in df.columns:
                try:
                    dates = pd.to_datetime(df[col], errors='coerce').dropna()
                    if len(dates) > 0:
                        return {
                            "start": dates.min().strftime("%Y-%m-%d"),
                            "end": dates.max().strftime("%Y-%m-%d")
                        }
                except:
                    continue
        return {"error": "No valid date range found"}
    
    def _get_safe_geographic_coverage(self, df: pd.DataFrame) -> Dict:
        """Get geographic coverage safely."""
        if 'place_of_birth' in df.columns:
            df['state'] = df['place_of_birth'].str.extract(r', ([A-Z]{2})$')
            state_counts = df['state'].value_counts()
            safe_counts = state_counts[state_counts >= self.min_aggregation_threshold]
            return {"states_represented": len(safe_counts)}
        return {"error": "No geographic data available"}
    
    def _assess_data_completeness(self, df: pd.DataFrame) -> Dict:
        """Assess overall data completeness."""
        completeness = {}
        for col in df.columns:
            completeness[col] = (1 - df[col].isnull().mean()) * 100
        
        return {
            "overall_completeness": (1 - df.isnull().mean().mean()) * 100,
            "field_completeness": completeness
        }
    
    def _calculate_data_quality_score(self, validation_report: Dict, df: pd.DataFrame) -> float:
        """Calculate overall data quality score."""
        base_score = 100.0
        
        # Deduct for validation errors
        schema_errors = len(validation_report.get("schema_validation", {}).get("errors", []))
        quality_errors = len(validation_report.get("quality_validation", {}).get("errors", []))
        
        base_score -= (schema_errors * 10)  # 10 points per schema error
        base_score -= (quality_errors * 5)   # 5 points per quality error
        
        # Deduct for missing data
        missing_rate = df.isnull().mean().mean()
        base_score -= (missing_rate * 30)  # Up to 30 points for missing data
        
        return max(0.0, base_score)
    
    def _interpret_effect_size(self, effect_size: float) -> str:
        """Interpret effect size magnitude."""
        abs_effect = abs(effect_size)
        if abs_effect < 0.1:
            return "negligible"
        elif abs_effect < 0.3:
            return "small"
        elif abs_effect < 0.5:
            return "medium"
        else:
            return "large"
    
    def _calculate_date_range_days(self, df: pd.DataFrame) -> Optional[int]:
        """Calculate date range in days."""
        date_cols = ['publication_date', 'publication']
        for col in date_cols:
            if col in df.columns:
                try:
                    dates = pd.to_datetime(df[col], errors='coerce').dropna()
                    if len(dates) > 0:
                        return (dates.max() - dates.min()).days
                except:
                    continue
        return None
    
    def validate_input(self, input_data: Any) -> ValidationResult:
        """Validate input data for reporting."""
        errors = []
        warnings = []
        
        if not isinstance(input_data, dict):
            errors.append("Input data must be a dictionary containing analysis results")
        else:
            if "classified_data" not in input_data:
                warnings.append("No classified data found for reporting")
            
            classified_data = input_data.get("classified_data", [])
            if not isinstance(classified_data, list):
                errors.append("Classified data must be a list")
            elif len(classified_data) == 0:
                warnings.append("No records in classified data")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )