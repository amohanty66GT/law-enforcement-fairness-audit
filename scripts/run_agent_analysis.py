#!/usr/bin/env python3
"""
Agent-based analysis script for the law enforcement fairness and bias audit system.
Uses the new agent-centered architecture for modular, deterministic analysis.
"""

import sys
import os
import argparse
from datetime import datetime
import logging
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.orchestrator import AgentOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/agent_analysis.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main execution function for agent-based analysis."""
    
    parser = argparse.ArgumentParser(description='Run agent-based fairness and bias audit analysis')
    
    # Data source options
    parser.add_argument('--data-source', choices=['fbi', 'sample', 'csv'], 
                       default='sample', help='Data source to use')
    parser.add_argument('--max-pages', type=int, default=10, 
                       help='Maximum pages to fetch from FBI API')
    parser.add_argument('--csv-file', type=str, 
                       help='Path to CSV file (if using csv data source)')
    
    # Analysis parameters
    parser.add_argument('--confidence-level', type=float, default=0.95,
                       help='Confidence level for statistical tests')
    parser.add_argument('--min-sample-size', type=int, default=30,
                       help='Minimum sample size for analysis')
    parser.add_argument('--aggregation-threshold', type=int, default=5,
                       help='Minimum aggregation threshold for privacy protection')
    
    # Output options
    parser.add_argument('--output-dir', default='output',
                       help='Directory for output files')
    parser.add_argument('--save-intermediate', action='store_true',
                       help='Save intermediate agent results')
    
    # Agent configuration
    parser.add_argument('--config-file', type=str,
                       help='Path to agent configuration file')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    logger.info("Starting agent-based fairness and bias audit analysis")
    logger.info(f"Configuration: {vars(args)}")
    
    try:
        # Load agent configuration
        agent_config = load_agent_configuration(args)
        
        # Create pipeline configuration
        pipeline_config = create_pipeline_configuration(args)
        
        # Initialize orchestrator
        orchestrator = AgentOrchestrator(agent_config)
        
        # Validate configuration
        validation_result = orchestrator.validate_pipeline_configuration(pipeline_config)
        if not validation_result["is_valid"]:
            logger.error("Pipeline configuration validation failed:")
            for error in validation_result["errors"]:
                logger.error(f"  - {error}")
            return 1
        
        if validation_result["warnings"]:
            logger.warning("Pipeline configuration warnings:")
            for warning in validation_result["warnings"]:
                logger.warning(f"  - {warning}")
        
        # Execute pipeline
        logger.info("Executing agent pipeline...")
        execution_result = orchestrator.execute_pipeline(pipeline_config)
        
        if execution_result["status"] == "success":
            logger.info(f"Pipeline execution successful: {execution_result['execution_id']}")
            
            # Save results
            orchestrator.save_execution_results(execution_result, args.output_dir)
            
            # Generate summary report
            generate_agent_summary_report(execution_result, args.output_dir)
            
            # Print execution summary
            print_execution_summary(execution_result)
            
            logger.info(f"Analysis complete! Results saved to: {args.output_dir}")
            return 0
            
        else:
            logger.error(f"Pipeline execution failed: {execution_result.get('error', 'Unknown error')}")
            
            # Save error details
            error_file = os.path.join(args.output_dir, f"error_{execution_result['execution_id']}.json")
            with open(error_file, 'w') as f:
                json.dump(execution_result, f, indent=2, default=str)
            
            return 1
            
    except Exception as e:
        logger.error(f"Analysis failed with unexpected error: {e}")
        raise

def load_agent_configuration(args) -> dict:
    """Load agent configuration from file or create default configuration."""
    
    if args.config_file and os.path.exists(args.config_file):
        logger.info(f"Loading agent configuration from: {args.config_file}")
        with open(args.config_file, 'r') as f:
            return json.load(f)
    
    # Default agent configuration
    logger.info("Using default agent configuration")
    return {
        "ingestion": {
            "max_retries": 3,
            "timeout_seconds": 30,
            "batch_size": 100
        },
        "validation": {
            "missing_threshold": 0.5,
            "drift_detection_window": 30,
            "quality_score_threshold": 0.7
        },
        "weapon_classification": {
            "confidence_threshold": 0.8,
            "unknown_threshold": 0.3
        },
        "serious_crime": {
            "crime_keywords": [
                "homicide", "murder", "aggravated assault", "robbery", 
                "kidnapping", "rape", "terrorism", "shooting"
            ]
        },
        "statistical": {
            "confidence_level": args.confidence_level,
            "min_sample_size": args.min_sample_size,
            "effect_size_threshold": 0.1
        },
        "trend": {
            "window_size": 12,
            "anomaly_threshold": 2.0,
            "min_periods": 6
        },
        "reporting": {
            "min_aggregation_threshold": args.aggregation_threshold,
            "max_categories_display": 10
        }
    }

def create_pipeline_configuration(args) -> dict:
    """Create pipeline configuration from command line arguments."""
    
    config = {
        "data_source": {
            "type": args.data_source,
            "max_pages": args.max_pages
        },
        "analysis_parameters": {
            "confidence_level": args.confidence_level,
            "min_sample_size": args.min_sample_size,
            "aggregation_threshold": args.aggregation_threshold
        },
        "output": {
            "directory": args.output_dir,
            "save_intermediate": args.save_intermediate
        },
        "execution": {
            "timestamp": datetime.now().isoformat(),
            "version": "1.0"
        }
    }
    
    # Add CSV file path if specified
    if args.csv_file:
        config["data_source"]["csv_file"] = args.csv_file
    
    return config

def generate_agent_summary_report(execution_result: dict, output_dir: str):
    """Generate a comprehensive summary report of the agent-based analysis."""
    
    report_file = os.path.join(output_dir, 'agent_analysis_report.md')
    execution_id = execution_result["execution_id"]
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Agent-Based Law Enforcement Data Fairness & Bias Audit Report\n\n")
        f.write(f"**Execution ID:** {execution_id}\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Status:** {execution_result['status'].upper()}\n\n")
        
        # Execution summary
        execution_record = execution_result.get("execution_record", {})
        f.write("## Execution Summary\n\n")
        f.write(f"- **Duration:** {execution_record.get('duration', 0):.2f} seconds\n")
        f.write(f"- **Agents Executed:** {len(execution_record.get('agent_results', {}))}\n")
        f.write(f"- **Errors:** {len(execution_record.get('errors', []))}\n")
        f.write(f"- **Warnings:** {len(execution_record.get('warnings', []))}\n\n")
        
        # Agent execution details
        f.write("## Agent Execution Details\n\n")
        agent_results = execution_record.get("agent_results", {})
        
        for agent_name, result in agent_results.items():
            status_icon = "✅" if result["status"] == "success" else "❌"
            f.write(f"### {status_icon} {agent_name.replace('_', ' ').title()} Agent\n")
            f.write(f"- **Status:** {result['status']}\n")
            f.write(f"- **Duration:** {result['duration']:.2f} seconds\n")
            f.write(f"- **Message Type:** {result['message_type']}\n")
            f.write(f"- **Data Size:** {result.get('data_size', 'N/A')}\n\n")
        
        # Results summary
        if execution_result["status"] == "success" and "results" in execution_result:
            f.write("## Analysis Results Summary\n\n")
            
            results = execution_result["results"]
            
            # Ingestion results
            if "ingestion" in results and results["ingestion"]:
                ingestion_data = results["ingestion"].data
                if isinstance(ingestion_data, list):
                    f.write(f"- **Records Ingested:** {len(ingestion_data)}\n")
            
            # Validation results
            if "validation" in results and results["validation"]:
                validation_data = results["validation"].data
                if isinstance(validation_data, dict):
                    f.write(f"- **Data Quality Status:** {validation_data.get('overall_status', 'Unknown')}\n")
                    if "quality_score" in validation_data:
                        f.write(f"- **Quality Score:** {validation_data['quality_score']:.2f}\n")
            
            # Statistical results
            if "statistical" in results and results["statistical"]:
                statistical_data = results["statistical"].data
                if isinstance(statistical_data, dict):
                    significant_tests = sum(1 for test_result in statistical_data.values() 
                                          if isinstance(test_result, dict) and test_result.get("significant", False))
                    f.write(f"- **Significant Statistical Results:** {significant_tests}\n")
            
            # Trend results
            if "trend" in results and results["trend"]:
                trend_data = results["trend"].data
                if isinstance(trend_data, dict) and "trend_results" in trend_data:
                    significant_trends = sum(1 for trend_result in trend_data["trend_results"].values()
                                           if isinstance(trend_result, dict) and trend_result.get("is_significant", False))
                    f.write(f"- **Significant Trends Detected:** {significant_trends}\n")
            
            # Reporting results
            if "reporting" in results and results["reporting"]:
                reporting_data = results["reporting"].data
                if isinstance(reporting_data, dict):
                    f.write(f"- **Report Sections Generated:** {len(reporting_data.get('report', {}))}\n")
                    f.write(f"- **Visualizations Created:** {len(reporting_data.get('visualizations', {}))}\n")
        
        # Errors and warnings
        errors = execution_record.get("errors", [])
        warnings = execution_record.get("warnings", [])
        
        if errors:
            f.write("## Errors\n\n")
            for error in errors:
                f.write(f"- **{error['agent']}:** {error['message']}\n")
            f.write("\n")
        
        if warnings:
            f.write("## Warnings\n\n")
            for warning in warnings:
                f.write(f"- **{warning['agent']}:** {warning['message']}\n")
            f.write("\n")
        
        # Methodology
        f.write("## Agent-Based Methodology\n\n")
        f.write("This analysis uses a modular agent-based architecture with the following components:\n\n")
        f.write("1. **Data Ingestion Agent:** Fetches and normalizes data from configured sources\n")
        f.write("2. **Validation & Drift Agent:** Validates data quality and detects distribution changes\n")
        f.write("3. **Weapon Classification Agent:** Categorizes weapon information using rule-based mapping\n")
        f.write("4. **Serious Crime Filter Agent:** Identifies and flags serious crimes\n")
        f.write("5. **Statistical Analysis Agent:** Performs bias detection using statistical tests\n")
        f.write("6. **Trend & Anomaly Agent:** Analyzes temporal patterns and detects anomalies\n")
        f.write("7. **Reporting & Visualization Agent:** Generates privacy-compliant reports and charts\n\n")
        
        # Ethical compliance
        f.write("## Ethical Compliance\n\n")
        f.write("- ✅ **Privacy Protection:** All analysis performed at aggregate level only\n")
        f.write("- ✅ **Aggregation Thresholds:** Minimum group sizes enforced to prevent individual inference\n")
        f.write("- ✅ **No Individual Tracking:** No personal identification or tracking performed\n")
        f.write("- ✅ **Transparency:** All agent decisions and methods documented\n")
        f.write("- ✅ **Bias Mitigation:** Statistical significance testing and effect size reporting\n\n")
        
        # Files generated
        f.write("## Generated Files\n\n")
        f.write(f"- `{execution_id}_results.json` - Complete execution results\n")
        f.write(f"- `{execution_id}_execution_log.json` - Detailed execution log\n")
        
        if execution_result["status"] == "success" and "results" in execution_result:
            for agent_name in execution_result["results"].keys():
                f.write(f"- `{execution_id}_{agent_name}.json` - {agent_name.replace('_', ' ').title()} agent output\n")
        
        f.write(f"- `agent_analysis_report.md` - This summary report\n\n")
    
    logger.info(f"Agent summary report saved to {report_file}")

def print_execution_summary(execution_result: dict):
    """Print a concise execution summary to console."""
    
    print("\n" + "="*60)
    print("AGENT-BASED ANALYSIS EXECUTION SUMMARY")
    print("="*60)
    
    execution_record = execution_result.get("execution_record", {})
    
    print(f"Execution ID: {execution_result['execution_id']}")
    print(f"Status: {execution_result['status'].upper()}")
    print(f"Duration: {execution_record.get('duration', 0):.2f} seconds")
    print(f"Agents Executed: {len(execution_record.get('agent_results', {}))}")
    
    # Agent status summary
    agent_results = execution_record.get("agent_results", {})
    successful_agents = sum(1 for result in agent_results.values() if result["status"] == "success")
    
    print(f"Successful Agents: {successful_agents}/{len(agent_results)}")
    
    if execution_record.get("errors"):
        print(f"Errors: {len(execution_record['errors'])}")
    
    if execution_record.get("warnings"):
        print(f"Warnings: {len(execution_record['warnings'])}")
    
    # Quick results summary
    if execution_result["status"] == "success" and "results" in execution_result:
        results = execution_result["results"]
        
        # Data ingested
        if "ingestion" in results and results["ingestion"]:
            ingestion_data = results["ingestion"].data
            if isinstance(ingestion_data, list):
                print(f"Records Processed: {len(ingestion_data)}")
        
        # Statistical significance
        if "statistical" in results and results["statistical"]:
            statistical_data = results["statistical"].data
            if isinstance(statistical_data, dict):
                significant_tests = sum(1 for test_result in statistical_data.values() 
                                      if isinstance(test_result, dict) and test_result.get("significant", False))
                print(f"Significant Statistical Results: {significant_tests}")
    
    print("="*60)
    print()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)