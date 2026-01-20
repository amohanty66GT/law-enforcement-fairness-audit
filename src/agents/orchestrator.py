"""
Agent Orchestrator - Coordinates the execution of all agents in the crime data analysis pipeline.
Manages agent communication, error handling, and result aggregation.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import os

from .base import BaseAgent, AgentExecutionContext, AgentMessage, AgentError
from .ingestion_agent import IngestionAgent
from .validation_agent import ValidationDriftAgent
from .weapon_classification_agent import WeaponClassificationAgent
from .serious_crime_agent import SeriousCrimeFilterAgent
from .statistical_agent import StatisticalAnalysisAgent
from .trend_agent import TrendAnomalyAgent
from .reporting_agent import ReportingVisualizationAgent

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """Orchestrates the execution of all agents in the analysis pipeline."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger("orchestrator")
        
        # Initialize agents
        self.agents = self._initialize_agents()
        
        # Execution tracking
        self.execution_history: List[Dict] = []
        
    def _initialize_agents(self) -> Dict[str, BaseAgent]:
        """Initialize all agents with configuration."""
        agents = {}
        
        try:
            # Agent configurations
            ingestion_config = self.config.get("ingestion", {})
            validation_config = self.config.get("validation", {})
            weapon_config = self.config.get("weapon_classification", {})
            crime_config = self.config.get("serious_crime", {})
            statistical_config = self.config.get("statistical", {})
            trend_config = self.config.get("trend", {})
            reporting_config = self.config.get("reporting", {})
            
            # Initialize agents in execution order
            agents["ingestion"] = IngestionAgent(ingestion_config)
            agents["validation"] = ValidationDriftAgent(validation_config)
            agents["weapon_classification"] = WeaponClassificationAgent(weapon_config)
            agents["serious_crime"] = SeriousCrimeFilterAgent(crime_config)
            agents["statistical"] = StatisticalAnalysisAgent(statistical_config)
            agents["trend"] = TrendAnomalyAgent(trend_config)
            agents["reporting"] = ReportingVisualizationAgent(reporting_config)
            
            self.logger.info(f"Initialized {len(agents)} agents successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agents: {e}")
            raise
        
        return agents
    
    def execute_pipeline(self, input_config: Dict) -> Dict[str, Any]:
        """Execute the complete agent pipeline."""
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.logger.info(f"Starting pipeline execution: {execution_id}")
        
        # Create execution context
        context = AgentExecutionContext(
            execution_id=execution_id,
            config=input_config,
            shared_data={},
            messages=[]
        )
        
        # Track execution
        execution_record = {
            "execution_id": execution_id,
            "start_time": datetime.now(),
            "config": input_config,
            "agent_results": {},
            "errors": [],
            "warnings": []
        }
        
        try:
            # Execute agents in sequence
            pipeline_results = self._execute_agent_sequence(context, execution_record)
            
            execution_record["end_time"] = datetime.now()
            execution_record["duration"] = (execution_record["end_time"] - execution_record["start_time"]).total_seconds()
            execution_record["status"] = "completed"
            
            self.logger.info(f"Pipeline execution completed: {execution_id} ({execution_record['duration']:.2f}s)")
            
            # Save execution record
            self.execution_history.append(execution_record)
            
            return {
                "execution_id": execution_id,
                "status": "success",
                "results": pipeline_results,
                "execution_record": execution_record,
                "context": context
            }
            
        except Exception as e:
            execution_record["end_time"] = datetime.now()
            execution_record["status"] = "failed"
            execution_record["error"] = str(e)
            
            self.logger.error(f"Pipeline execution failed: {execution_id} - {e}")
            
            self.execution_history.append(execution_record)
            
            return {
                "execution_id": execution_id,
                "status": "error",
                "error": str(e),
                "execution_record": execution_record
            }
    
    def _execute_agent_sequence(self, context: AgentExecutionContext, execution_record: Dict) -> Dict[str, Any]:
        """Execute agents in the correct sequence with data flow."""
        results = {}
        
        # Step 1: Data Ingestion
        self.logger.info("Step 1: Data Ingestion")
        ingestion_result = self._execute_agent_with_error_handling(
            "ingestion", context, context.config, execution_record
        )
        results["ingestion"] = ingestion_result
        
        # Extract raw data for next steps
        raw_data = ingestion_result.data if ingestion_result else []
        if not raw_data:
            raise AgentError("orchestrator", "No data ingested - cannot continue pipeline")
        
        # Step 2: Validation & Drift Detection
        self.logger.info("Step 2: Validation & Drift Detection")
        validation_result = self._execute_agent_with_error_handling(
            "validation", context, raw_data, execution_record
        )
        results["validation"] = validation_result
        
        # Step 3: Weapon Classification
        self.logger.info("Step 3: Weapon Classification")
        weapon_result = self._execute_agent_with_error_handling(
            "weapon_classification", context, raw_data, execution_record
        )
        results["weapon_classification"] = weapon_result
        
        # Extract classified data
        classified_data = weapon_result.data if weapon_result else raw_data
        
        # Step 4: Serious Crime Filtering
        self.logger.info("Step 4: Serious Crime Filtering")
        crime_result = self._execute_agent_with_error_handling(
            "serious_crime", context, classified_data, execution_record
        )
        results["serious_crime"] = crime_result
        
        # Extract final processed data
        processed_data = crime_result.data if crime_result else classified_data
        
        # Step 5: Statistical Analysis
        self.logger.info("Step 5: Statistical Analysis")
        statistical_result = self._execute_agent_with_error_handling(
            "statistical", context, processed_data, execution_record
        )
        results["statistical"] = statistical_result
        
        # Step 6: Trend & Anomaly Detection
        self.logger.info("Step 6: Trend & Anomaly Detection")
        trend_result = self._execute_agent_with_error_handling(
            "trend", context, processed_data, execution_record
        )
        results["trend"] = trend_result
        
        # Step 7: Reporting & Visualization
        self.logger.info("Step 7: Reporting & Visualization")
        
        # Prepare comprehensive input for reporting agent
        reporting_input = {
            "classified_data": processed_data,
            "validation_report": validation_result.data if validation_result else {},
            "statistical_results": statistical_result.data if statistical_result else {},
            "trend_results": trend_result.data if trend_result else {}
        }
        
        reporting_result = self._execute_agent_with_error_handling(
            "reporting", context, reporting_input, execution_record
        )
        results["reporting"] = reporting_result
        
        return results
    
    def _execute_agent_with_error_handling(self, agent_name: str, context: AgentExecutionContext, 
                                         input_data: Any, execution_record: Dict) -> Optional[AgentMessage]:
        """Execute a single agent with comprehensive error handling."""
        try:
            agent = self.agents[agent_name]
            
            # Validate input
            validation_result = agent.validate_input(input_data)
            if not validation_result.is_valid:
                error_msg = f"Input validation failed for {agent_name}: {validation_result.errors}"
                self.logger.error(error_msg)
                execution_record["errors"].append({
                    "agent": agent_name,
                    "type": "validation_error",
                    "message": error_msg,
                    "details": validation_result.errors
                })
                return None
            
            # Log warnings
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    self.logger.warning(f"{agent_name}: {warning}")
                    execution_record["warnings"].append({
                        "agent": agent_name,
                        "message": warning
                    })
            
            # Execute agent
            start_time = datetime.now()
            result = agent.execute(context, input_data)
            end_time = datetime.now()
            
            # Record execution details
            execution_record["agent_results"][agent_name] = {
                "status": "success",
                "start_time": start_time,
                "end_time": end_time,
                "duration": (end_time - start_time).total_seconds(),
                "message_type": result.message_type,
                "data_size": len(result.data) if isinstance(result.data, (list, dict)) else 1
            }
            
            # Add message to context
            context.messages.append(result)
            
            self.logger.info(f"Agent {agent_name} completed successfully in {(end_time - start_time).total_seconds():.2f}s")
            
            return result
            
        except AgentError as e:
            self.logger.error(f"Agent {agent_name} failed: {e}")
            execution_record["errors"].append({
                "agent": agent_name,
                "type": "agent_error",
                "message": str(e),
                "details": e.details
            })
            return None
            
        except Exception as e:
            self.logger.error(f"Unexpected error in agent {agent_name}: {e}")
            execution_record["errors"].append({
                "agent": agent_name,
                "type": "unexpected_error",
                "message": str(e)
            })
            return None
    
    def get_execution_summary(self, execution_id: Optional[str] = None) -> Dict:
        """Get summary of pipeline execution(s)."""
        if execution_id:
            # Get specific execution
            for record in self.execution_history:
                if record["execution_id"] == execution_id:
                    return self._format_execution_summary(record)
            return {"error": f"Execution {execution_id} not found"}
        else:
            # Get summary of all executions
            return {
                "total_executions": len(self.execution_history),
                "successful_executions": len([r for r in self.execution_history if r["status"] == "completed"]),
                "failed_executions": len([r for r in self.execution_history if r["status"] == "failed"]),
                "recent_executions": [self._format_execution_summary(r) for r in self.execution_history[-5:]]
            }
    
    def _format_execution_summary(self, record: Dict) -> Dict:
        """Format execution record for summary display."""
        return {
            "execution_id": record["execution_id"],
            "status": record["status"],
            "start_time": record["start_time"].isoformat(),
            "duration": record.get("duration", 0),
            "agents_executed": len(record["agent_results"]),
            "errors": len(record["errors"]),
            "warnings": len(record["warnings"])
        }
    
    def save_execution_results(self, execution_result: Dict, output_dir: str) -> None:
        """Save execution results to files."""
        os.makedirs(output_dir, exist_ok=True)
        
        execution_id = execution_result["execution_id"]
        
        # Save main results
        results_file = os.path.join(output_dir, f"{execution_id}_results.json")
        with open(results_file, 'w') as f:
            # Convert datetime objects for JSON serialization
            serializable_result = self._make_json_serializable(execution_result)
            json.dump(serializable_result, f, indent=2, default=str)
        
        # Save individual agent outputs
        if "results" in execution_result:
            for agent_name, agent_result in execution_result["results"].items():
                if agent_result and hasattr(agent_result, 'data'):
                    agent_file = os.path.join(output_dir, f"{execution_id}_{agent_name}.json")
                    with open(agent_file, 'w') as f:
                        serializable_data = self._make_json_serializable(agent_result.data)
                        json.dump(serializable_data, f, indent=2, default=str)
        
        # Save execution log
        log_file = os.path.join(output_dir, f"{execution_id}_execution_log.json")
        with open(log_file, 'w') as f:
            log_data = execution_result.get("execution_record", {})
            serializable_log = self._make_json_serializable(log_data)
            json.dump(serializable_log, f, indent=2, default=str)
        
        self.logger.info(f"Execution results saved to {output_dir}")
    
    def _make_json_serializable(self, obj: Any) -> Any:
        """Convert objects to JSON-serializable format."""
        if isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif hasattr(obj, 'isoformat'):  # datetime objects
            return obj.isoformat()
        elif hasattr(obj, 'item'):  # numpy scalars
            return obj.item()
        elif hasattr(obj, 'tolist'):  # numpy arrays
            return obj.tolist()
        elif hasattr(obj, '__dict__'):  # custom objects
            return self._make_json_serializable(obj.__dict__)
        else:
            return obj
    
    def validate_pipeline_configuration(self, config: Dict) -> Dict:
        """Validate pipeline configuration before execution."""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check required configuration sections
        required_sections = ["data_source", "analysis_parameters"]
        for section in required_sections:
            if section not in config:
                validation_result["errors"].append(f"Missing required configuration section: {section}")
        
        # Validate data source configuration
        if "data_source" in config:
            data_source = config["data_source"]
            if "type" not in data_source:
                validation_result["errors"].append("Data source type not specified")
            elif data_source["type"] not in ["fbi_api", "sample", "csv_file"]:
                validation_result["errors"].append(f"Invalid data source type: {data_source['type']}")
        
        # Validate analysis parameters
        if "analysis_parameters" in config:
            params = config["analysis_parameters"]
            
            # Check confidence level
            if "confidence_level" in params:
                conf_level = params["confidence_level"]
                if not (0.5 <= conf_level <= 0.99):
                    validation_result["errors"].append("Confidence level must be between 0.5 and 0.99")
            
            # Check minimum sample size
            if "min_sample_size" in params:
                min_size = params["min_sample_size"]
                if not isinstance(min_size, int) or min_size < 1:
                    validation_result["errors"].append("Minimum sample size must be a positive integer")
        
        # Set validity flag
        validation_result["is_valid"] = len(validation_result["errors"]) == 0
        
        return validation_result
    
    def get_agent_status(self) -> Dict:
        """Get status of all agents."""
        status = {}
        
        for agent_name, agent in self.agents.items():
            status[agent_name] = {
                "agent_id": agent.agent_id,
                "config": agent.config,
                "initialized": True
            }
        
        return status