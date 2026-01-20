#!/usr/bin/env python3
"""
Comparison script to demonstrate both traditional and agent-based analysis approaches.
Shows the benefits of the new agent-centered architecture.
"""

import sys
import os
import argparse
from datetime import datetime
import logging
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.orchestrator import AgentOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to compare analysis approaches."""
    
    parser = argparse.ArgumentParser(description='Compare traditional vs agent-based analysis')
    parser.add_argument('--approach', choices=['traditional', 'agents', 'both'], 
                       default='both', help='Which approach to run')
    parser.add_argument('--output-dir', default='output_comparison',
                       help='Directory for output files')
    
    args = parser.parse_args()
    
    # Create output directories
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    logger.info("Starting analysis approach comparison")
    
    results = {}
    
    if args.approach in ['traditional', 'both']:
        logger.info("Running traditional analysis approach...")
        results['traditional'] = run_traditional_analysis(args.output_dir)
    
    if args.approach in ['agents', 'both']:
        logger.info("Running agent-based analysis approach...")
        results['agents'] = run_agent_based_analysis(args.output_dir)
    
    # Generate comparison report
    if args.approach == 'both':
        generate_comparison_report(results, args.output_dir)
    
    logger.info("Analysis comparison complete!")

def run_traditional_analysis(output_dir):
    """Run the traditional monolithic analysis approach."""
    
    start_time = time.time()
    
    try:
        # Import traditional modules
        from data_ingestion.fbi_wanted import FBIWantedIngestion
        from data_processing.feature_engineering import FeatureEngineer
        from analysis.bias_metrics import BiasAnalyzer
        from analysis.weapons_analysis import WeaponsAnalyzer
        
        logger.info("Traditional: Starting data ingestion...")
        
        # Generate sample data (same as traditional script)
        import pandas as pd
        import numpy as np
        
        np.random.seed(42)
        
        # Create sample data
        sample_data = generate_sample_data_traditional()
        
        logger.info(f"Traditional: Ingested {len(sample_data)} records")
        
        # Feature engineering
        logger.info("Traditional: Feature engineering...")
        engineer = FeatureEngineer()
        processed_df = engineer.engineer_features(sample_data)
        
        # Analysis
        logger.info("Traditional: Running bias analysis...")
        analyzer = BiasAnalyzer(confidence_level=0.95)
        
        geo_results = analyzer.analyze_geographic_bias(processed_df)
        cat_results = analyzer.analyze_categorical_bias(processed_df)
        temporal_results = analyzer.analyze_temporal_trends(processed_df)
        
        # Weapons analysis
        logger.info("Traditional: Running weapons analysis...")
        weapons_analyzer = WeaponsAnalyzer()
        weapons_results = weapons_analyzer.analyze_weapon_patterns(processed_df)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Save results
        traditional_output = os.path.join(output_dir, 'traditional')
        os.makedirs(traditional_output, exist_ok=True)
        
        processed_df.to_csv(os.path.join(traditional_output, 'processed_data.csv'), index=False)
        
        return {
            'status': 'success',
            'duration': duration,
            'records_processed': len(processed_df),
            'analyses_completed': 4,
            'output_files': ['processed_data.csv'],
            'approach': 'monolithic'
        }
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        
        logger.error(f"Traditional analysis failed: {e}")
        
        return {
            'status': 'error',
            'duration': duration,
            'error': str(e),
            'approach': 'monolithic'
        }

def run_agent_based_analysis(output_dir):
    """Run the new agent-based analysis approach."""
    
    start_time = time.time()
    
    try:
        # Agent configuration
        agent_config = {
            "ingestion": {"max_retries": 3, "timeout_seconds": 30},
            "validation": {"missing_threshold": 0.5, "quality_score_threshold": 0.7},
            "weapon_classification": {"confidence_threshold": 0.8},
            "serious_crime": {"crime_keywords": ["homicide", "assault", "robbery"]},
            "statistical": {"confidence_level": 0.95, "min_sample_size": 30},
            "trend": {"window_size": 12, "anomaly_threshold": 2.0},
            "reporting": {"min_aggregation_threshold": 5, "max_categories_display": 10}
        }
        
        # Pipeline configuration
        pipeline_config = {
            "data_source": {"type": "sample", "max_pages": 10},
            "analysis_parameters": {
                "confidence_level": 0.95,
                "min_sample_size": 30,
                "aggregation_threshold": 5
            },
            "output": {"directory": output_dir, "save_intermediate": True}
        }
        
        # Initialize orchestrator
        orchestrator = AgentOrchestrator(agent_config)
        
        # Execute pipeline
        execution_result = orchestrator.execute_pipeline(pipeline_config)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if execution_result["status"] == "success":
            # Save results
            agent_output = os.path.join(output_dir, 'agents')
            os.makedirs(agent_output, exist_ok=True)
            
            orchestrator.save_execution_results(execution_result, agent_output)
            
            # Count successful agents
            execution_record = execution_result.get("execution_record", {})
            agent_results = execution_record.get("agent_results", {})
            successful_agents = sum(1 for result in agent_results.values() 
                                  if result["status"] == "success")
            
            # Count output files
            output_files = []
            execution_id = execution_result["execution_id"]
            for agent_name in agent_results.keys():
                output_files.append(f"{execution_id}_{agent_name}.json")
            output_files.extend([f"{execution_id}_results.json", f"{execution_id}_execution_log.json"])
            
            return {
                'status': 'success',
                'duration': duration,
                'execution_id': execution_result["execution_id"],
                'agents_executed': len(agent_results),
                'successful_agents': successful_agents,
                'output_files': output_files,
                'approach': 'agent-based',
                'execution_record': execution_record
            }
        else:
            return {
                'status': 'error',
                'duration': duration,
                'error': execution_result.get('error', 'Unknown error'),
                'approach': 'agent-based'
            }
            
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        
        logger.error(f"Agent-based analysis failed: {e}")
        
        return {
            'status': 'error',
            'duration': duration,
            'error': str(e),
            'approach': 'agent-based'
        }

def generate_sample_data_traditional():
    """Generate sample data using traditional approach."""
    import pandas as pd
    import numpy as np
    
    np.random.seed(42)
    
    states = ['CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI']
    
    crime_scenarios = [
        {'type': 'Armed Robbery', 'desc': 'Suspect robbed bank with handgun'},
        {'type': 'Assault', 'desc': 'Victim attacked with knife'},
        {'type': 'Fraud', 'desc': 'Financial fraud scheme'},
        {'type': 'Drug Trafficking', 'desc': 'Large quantity of narcotics seized'},
        {'type': 'Cyber Crime', 'desc': 'Computer fraud targeting victims'}
    ]
    
    n_records = 500
    sample_data = []
    
    for i in range(n_records):
        state = np.random.choice(states)
        scenario = np.random.choice(crime_scenarios)
        
        pub_date = pd.Timestamp('2023-01-01') + pd.Timedelta(days=np.random.randint(0, 365))
        
        sample_data.append({
            'uid': f'sample_{i:04d}',
            'title': f'{scenario["type"]} Case {i}',
            'description': scenario['desc'],
            'place_of_birth': f'City, {state}',
            'publication_date': pub_date,
            'modified_date': pub_date + pd.Timedelta(days=np.random.randint(0, 30)),
            'ingestion_date': pd.Timestamp.now(),
            'reward_text': f'${np.random.choice([5000, 10000, 25000])}' if np.random.random() > 0.4 else None,
            'images': [f'image_{i}.jpg'] if np.random.random() > 0.6 else []
        })
    
    return pd.DataFrame(sample_data)

def generate_comparison_report(results, output_dir):
    """Generate a comparison report between approaches."""
    
    report_file = os.path.join(output_dir, 'approach_comparison_report.md')
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Analysis Approach Comparison Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Executive Summary
        f.write("## Executive Summary\n\n")
        f.write("This report compares the traditional monolithic analysis approach with the new agent-based architecture for law enforcement data fairness and bias auditing.\n\n")
        
        # Performance Comparison
        f.write("## Performance Comparison\n\n")
        
        traditional = results.get('traditional', {})
        agents = results.get('agents', {})
        
        f.write("| Metric | Traditional | Agent-Based | Improvement |\n")
        f.write("|--------|-------------|-------------|-------------|\n")
        
        # Duration comparison
        trad_duration = traditional.get('duration', 0)
        agent_duration = agents.get('duration', 0)
        
        f.write(f"| Execution Time | {trad_duration:.2f}s | {agent_duration:.2f}s | ")
        if trad_duration > 0 and agent_duration > 0:
            improvement = ((trad_duration - agent_duration) / trad_duration) * 100
            f.write(f"{improvement:+.1f}% |\n")
        else:
            f.write("N/A |\n")
        
        # Status comparison
        f.write(f"| Status | {traditional.get('status', 'N/A')} | {agents.get('status', 'N/A')} | - |\n")
        
        # Output files comparison
        trad_files = len(traditional.get('output_files', []))
        agent_files = len(agents.get('output_files', []))
        f.write(f"| Output Files | {trad_files} | {agent_files} | {agent_files - trad_files:+d} |\n")
        
        f.write("\n")
        
        # Architecture Comparison
        f.write("## Architecture Comparison\n\n")
        
        f.write("### Traditional Monolithic Approach\n")
        f.write("- **Structure:** Single-threaded, sequential processing\n")
        f.write("- **Error Handling:** Fail-fast, entire pipeline stops on error\n")
        f.write("- **Modularity:** Tightly coupled components\n")
        f.write("- **Transparency:** Limited visibility into individual steps\n")
        f.write("- **Extensibility:** Difficult to add new analysis types\n")
        f.write("- **Testing:** Integration testing only\n\n")
        
        f.write("### Agent-Based Architecture\n")
        f.write("- **Structure:** Modular agents with single responsibilities\n")
        f.write("- **Error Handling:** Graceful degradation, continues on non-critical errors\n")
        f.write("- **Modularity:** Loosely coupled, independently testable agents\n")
        f.write("- **Transparency:** Full visibility into each agent's execution\n")
        f.write("- **Extensibility:** Easy to add, remove, or modify agents\n")
        f.write("- **Testing:** Unit and integration testing for each agent\n\n")
        
        # Detailed Results
        if traditional.get('status') == 'success':
            f.write("### Traditional Approach Results\n")
            f.write(f"- **Records Processed:** {traditional.get('records_processed', 'N/A')}\n")
            f.write(f"- **Analyses Completed:** {traditional.get('analyses_completed', 'N/A')}\n")
            f.write(f"- **Duration:** {traditional.get('duration', 0):.2f} seconds\n\n")
        
        if agents.get('status') == 'success':
            f.write("### Agent-Based Approach Results\n")
            f.write(f"- **Execution ID:** {agents.get('execution_id', 'N/A')}\n")
            f.write(f"- **Agents Executed:** {agents.get('agents_executed', 'N/A')}\n")
            f.write(f"- **Successful Agents:** {agents.get('successful_agents', 'N/A')}\n")
            f.write(f"- **Duration:** {agents.get('duration', 0):.2f} seconds\n")
            
            # Agent execution details
            if 'execution_record' in agents:
                execution_record = agents['execution_record']
                agent_results = execution_record.get('agent_results', {})
                
                f.write("\n**Agent Execution Details:**\n")
                for agent_name, result in agent_results.items():
                    status_icon = "✅" if result["status"] == "success" else "❌"
                    f.write(f"- {status_icon} {agent_name.replace('_', ' ').title()}: {result['duration']:.2f}s\n")
            
            f.write("\n")
        
        # Error Analysis
        errors = []
        if traditional.get('status') == 'error':
            errors.append(f"**Traditional:** {traditional.get('error', 'Unknown error')}")
        
        if agents.get('status') == 'error':
            errors.append(f"**Agent-Based:** {agents.get('error', 'Unknown error')}")
        elif 'execution_record' in agents:
            execution_errors = agents['execution_record'].get('errors', [])
            if execution_errors:
                for error in execution_errors:
                    errors.append(f"**Agent {error['agent']}:** {error['message']}")
        
        if errors:
            f.write("## Error Analysis\n\n")
            for error in errors:
                f.write(f"- {error}\n")
            f.write("\n")
        
        # Recommendations
        f.write("## Recommendations\n\n")
        
        if agents.get('status') == 'success' and traditional.get('status') == 'success':
            f.write("✅ **Recommendation: Adopt Agent-Based Architecture**\n\n")
            f.write("The agent-based approach provides:\n")
            f.write("- Better error handling and recovery\n")
            f.write("- Improved modularity and maintainability\n")
            f.write("- Enhanced transparency and debugging capabilities\n")
            f.write("- Easier testing and validation\n")
            f.write("- Greater extensibility for future enhancements\n\n")
        elif agents.get('status') == 'success':
            f.write("✅ **Agent-based approach succeeded where traditional failed**\n\n")
        elif traditional.get('status') == 'success':
            f.write("⚠️ **Traditional approach succeeded where agent-based failed**\n\n")
            f.write("Consider debugging agent implementation issues.\n\n")
        else:
            f.write("❌ **Both approaches failed**\n\n")
            f.write("Review system configuration and data sources.\n\n")
        
        # Future Enhancements
        f.write("## Future Enhancements for Agent Architecture\n\n")
        f.write("- **Parallel Execution:** Run independent agents concurrently\n")
        f.write("- **Dynamic Configuration:** Runtime agent configuration updates\n")
        f.write("- **Agent Monitoring:** Real-time agent health and performance monitoring\n")
        f.write("- **Result Caching:** Cache agent results for faster re-execution\n")
        f.write("- **Agent Marketplace:** Plugin system for community-contributed agents\n")
    
    logger.info(f"Comparison report saved to {report_file}")

if __name__ == "__main__":
    main()