#!/usr/bin/env python3
"""
Integration tests for the agent-based crime data analysis system.
Tests the complete pipeline and individual agent interactions.
"""

import sys
import os
import unittest
from datetime import datetime
import tempfile
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agents.orchestrator import AgentOrchestrator
from agents.base import AgentExecutionContext
from agents.ingestion_agent import IngestionAgent
from agents.validation_agent import ValidationDriftAgent
from agents.weapon_classification_agent import WeaponClassificationAgent
from agents.serious_crime_agent import SeriousCrimeFilterAgent
from agents.statistical_agent import StatisticalAnalysisAgent
from agents.trend_agent import TrendAnomalyAgent
from agents.reporting_agent import ReportingVisualizationAgent

class TestAgentIntegration(unittest.TestCase):
    """Test suite for agent integration and pipeline execution."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_config = {
            "ingestion": {"max_retries": 2, "timeout_seconds": 10},
            "validation": {"missing_threshold": 0.5, "quality_score_threshold": 0.6},
            "weapon_classification": {"confidence_threshold": 0.7},
            "serious_crime": {"crime_keywords": ["homicide", "assault", "robbery"]},
            "statistical": {"confidence_level": 0.95, "min_sample_size": 10},
            "trend": {"window_size": 6, "anomaly_threshold": 2.0},
            "reporting": {"min_aggregation_threshold": 3, "max_categories_display": 5}
        }
        
        self.pipeline_config = {
            "data_source": {"type": "sample", "max_pages": 1},
            "analysis_parameters": {
                "confidence_level": 0.95,
                "min_sample_size": 10,
                "aggregation_threshold": 3
            },
            "output": {"directory": "test_output", "save_intermediate": True}
        }
        
        # Create temporary output directory
        self.temp_dir = tempfile.mkdtemp()
        self.pipeline_config["output"]["directory"] = self.temp_dir
    
    def tearDown(self):
        """Clean up test environment."""
        # Clean up temporary files
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_orchestrator_initialization(self):
        """Test that orchestrator initializes all agents correctly."""
        orchestrator = AgentOrchestrator(self.test_config)
        
        # Check that all expected agents are initialized
        expected_agents = [
            "ingestion", "validation", "weapon_classification", 
            "serious_crime", "statistical", "trend", "reporting"
        ]
        
        for agent_name in expected_agents:
            self.assertIn(agent_name, orchestrator.agents)
            self.assertIsNotNone(orchestrator.agents[agent_name])
        
        # Check agent status
        status = orchestrator.get_agent_status()
        self.assertEqual(len(status), len(expected_agents))
        
        for agent_name in expected_agents:
            self.assertIn(agent_name, status)
            self.assertTrue(status[agent_name]["initialized"])
    
    def test_pipeline_configuration_validation(self):
        """Test pipeline configuration validation."""
        orchestrator = AgentOrchestrator(self.test_config)
        
        # Test valid configuration
        valid_result = orchestrator.validate_pipeline_configuration(self.pipeline_config)
        self.assertTrue(valid_result["is_valid"])
        self.assertEqual(len(valid_result["errors"]), 0)
        
        # Test invalid configuration - missing required sections
        invalid_config = {"invalid": "config"}
        invalid_result = orchestrator.validate_pipeline_configuration(invalid_config)
        self.assertFalse(invalid_result["is_valid"])
        self.assertGreater(len(invalid_result["errors"]), 0)
        
        # Test invalid confidence level
        bad_confidence_config = self.pipeline_config.copy()
        bad_confidence_config["analysis_parameters"]["confidence_level"] = 1.5
        bad_result = orchestrator.validate_pipeline_configuration(bad_confidence_config)
        self.assertFalse(bad_result["is_valid"])
    
    def test_individual_agent_execution(self):
        """Test individual agent execution with sample data."""
        
        # Create sample data
        sample_data = [
            {
                "uid": "test_001",
                "title": "Armed Robbery Case",
                "description": "Suspect robbed bank with handgun",
                "place_of_birth": "Los Angeles, CA",
                "publication_date": "2023-01-15",
                "modified_date": "2023-01-16",
                "ingestion_date": datetime.now().isoformat()
            },
            {
                "uid": "test_002", 
                "title": "Fraud Investigation",
                "description": "Financial fraud scheme targeting elderly",
                "place_of_birth": "Houston, TX",
                "publication_date": "2023-02-10",
                "modified_date": "2023-02-11",
                "ingestion_date": datetime.now().isoformat()
            }
        ]
        
        # Create execution context
        context = AgentExecutionContext(
            execution_id="test_exec_001",
            config=self.pipeline_config,
            shared_data={},
            messages=[]
        )
        
        # Test Validation Agent
        validation_agent = ValidationDriftAgent(self.test_config["validation"])
        validation_result = validation_agent.execute(context, sample_data)
        
        self.assertIsNotNone(validation_result)
        self.assertEqual(validation_result.message_type, "validation_report")
        self.assertIsInstance(validation_result.data, dict)
        
        # Test Weapon Classification Agent
        weapon_agent = WeaponClassificationAgent(self.test_config["weapon_classification"])
        weapon_result = weapon_agent.execute(context, sample_data)
        
        self.assertIsNotNone(weapon_result)
        self.assertEqual(weapon_result.message_type, "classified_data")
        self.assertIsInstance(weapon_result.data, list)
        
        # Verify weapon classification was added
        classified_data = weapon_result.data
        for record in classified_data:
            self.assertIn("weapon_category", record)
            self.assertIn("weapon_raw", record)
        
        # Test Serious Crime Agent
        crime_agent = SeriousCrimeFilterAgent(self.test_config["serious_crime"])
        crime_result = crime_agent.execute(context, classified_data)
        
        self.assertIsNotNone(crime_result)
        self.assertEqual(crime_result.message_type, "processed_data")
        self.assertIsInstance(crime_result.data, list)
        
        # Verify severity flag was added
        processed_data = crime_result.data
        for record in processed_data:
            self.assertIn("severity_flag", record)
    
    def test_complete_pipeline_execution(self):
        """Test complete pipeline execution from start to finish."""
        orchestrator = AgentOrchestrator(self.test_config)
        
        # Execute pipeline
        execution_result = orchestrator.execute_pipeline(self.pipeline_config)
        
        # Check execution status
        self.assertEqual(execution_result["status"], "success")
        self.assertIn("execution_id", execution_result)
        self.assertIn("results", execution_result)
        
        # Check that all agents executed
        results = execution_result["results"]
        expected_agents = [
            "ingestion", "validation", "weapon_classification",
            "serious_crime", "statistical", "trend", "reporting"
        ]
        
        for agent_name in expected_agents:
            self.assertIn(agent_name, results)
            if results[agent_name]:  # Some agents might return None on errors
                self.assertIsNotNone(results[agent_name].data)
        
        # Check execution record
        execution_record = execution_result["execution_record"]
        self.assertEqual(execution_record["status"], "completed")
        self.assertIn("duration", execution_record)
        self.assertGreater(execution_record["duration"], 0)
    
    def test_agent_error_handling(self):
        """Test agent error handling and recovery."""
        
        # Create configuration that will cause validation errors
        bad_config = self.test_config.copy()
        bad_config["validation"]["missing_threshold"] = -1  # Invalid threshold
        
        orchestrator = AgentOrchestrator(bad_config)
        
        # Execute with invalid data
        invalid_data_config = {
            "data_source": {"type": "invalid_source"},
            "analysis_parameters": {"confidence_level": 2.0}  # Invalid confidence level
        }
        
        execution_result = orchestrator.execute_pipeline(invalid_data_config)
        
        # Should handle errors gracefully
        self.assertIn("status", execution_result)
        
        # Check execution record for error details
        execution_record = execution_result.get("execution_record", {})
        if "errors" in execution_record:
            self.assertIsInstance(execution_record["errors"], list)
    
    def test_data_flow_between_agents(self):
        """Test that data flows correctly between agents."""
        orchestrator = AgentOrchestrator(self.test_config)
        
        # Execute pipeline and check data transformations
        execution_result = orchestrator.execute_pipeline(self.pipeline_config)
        
        if execution_result["status"] == "success":
            results = execution_result["results"]
            
            # Check ingestion output
            if "ingestion" in results and results["ingestion"]:
                ingestion_data = results["ingestion"].data
                self.assertIsInstance(ingestion_data, list)
                if len(ingestion_data) > 0:
                    # Should have basic fields
                    sample_record = ingestion_data[0]
                    self.assertIn("uid", sample_record)
                    self.assertIn("title", sample_record)
            
            # Check weapon classification output
            if "weapon_classification" in results and results["weapon_classification"]:
                weapon_data = results["weapon_classification"].data
                self.assertIsInstance(weapon_data, list)
                if len(weapon_data) > 0:
                    # Should have weapon fields added
                    sample_record = weapon_data[0]
                    self.assertIn("weapon_category", sample_record)
                    self.assertIn("weapon_raw", sample_record)
            
            # Check serious crime output
            if "serious_crime" in results and results["serious_crime"]:
                crime_data = results["serious_crime"].data
                self.assertIsInstance(crime_data, list)
                if len(crime_data) > 0:
                    # Should have severity flag added
                    sample_record = crime_data[0]
                    self.assertIn("severity_flag", sample_record)
    
    def test_result_serialization(self):
        """Test that results can be properly serialized and saved."""
        orchestrator = AgentOrchestrator(self.test_config)
        
        execution_result = orchestrator.execute_pipeline(self.pipeline_config)
        
        if execution_result["status"] == "success":
            # Test saving results
            try:
                orchestrator.save_execution_results(execution_result, self.temp_dir)
                
                # Check that files were created
                execution_id = execution_result["execution_id"]
                results_file = os.path.join(self.temp_dir, f"{execution_id}_results.json")
                log_file = os.path.join(self.temp_dir, f"{execution_id}_execution_log.json")
                
                self.assertTrue(os.path.exists(results_file))
                self.assertTrue(os.path.exists(log_file))
                
                # Test that files contain valid JSON
                with open(results_file, 'r') as f:
                    saved_results = json.load(f)
                    self.assertIn("execution_id", saved_results)
                
                with open(log_file, 'r') as f:
                    saved_log = json.load(f)
                    self.assertIn("execution_id", saved_log)
                    
            except Exception as e:
                self.fail(f"Result serialization failed: {e}")
    
    def test_execution_summary(self):
        """Test execution summary generation."""
        orchestrator = AgentOrchestrator(self.test_config)
        
        # Execute pipeline
        execution_result = orchestrator.execute_pipeline(self.pipeline_config)
        execution_id = execution_result["execution_id"]
        
        # Test getting specific execution summary
        specific_summary = orchestrator.get_execution_summary(execution_id)
        self.assertIn("execution_id", specific_summary)
        self.assertEqual(specific_summary["execution_id"], execution_id)
        
        # Test getting all executions summary
        all_summary = orchestrator.get_execution_summary()
        self.assertIn("total_executions", all_summary)
        self.assertGreater(all_summary["total_executions"], 0)
        self.assertIn("recent_executions", all_summary)
    
    def test_privacy_compliance(self):
        """Test that privacy and ethical constraints are enforced."""
        orchestrator = AgentOrchestrator(self.test_config)
        
        execution_result = orchestrator.execute_pipeline(self.pipeline_config)
        
        if execution_result["status"] == "success":
            results = execution_result["results"]
            
            # Check reporting agent enforces aggregation thresholds
            if "reporting" in results and results["reporting"]:
                reporting_data = results["reporting"].data
                
                # Should have privacy compliance metadata
                if "metadata" in reporting_data:
                    metadata = reporting_data["metadata"]
                    self.assertTrue(metadata.get("privacy_compliant", False))
                    self.assertIn("aggregation_threshold", metadata)
                
                # Check that visualizations respect thresholds
                if "visualizations" in reporting_data:
                    visualizations = reporting_data["visualizations"]
                    for viz_name, viz_data in visualizations.items():
                        if isinstance(viz_data, dict) and "layout" in viz_data:
                            # Should have notes about aggregation thresholds
                            layout = viz_data["layout"]
                            if "note" in layout:
                                self.assertIn("threshold", layout["note"].lower())

class TestAgentCommunication(unittest.TestCase):
    """Test agent communication and message passing."""
    
    def test_agent_message_structure(self):
        """Test that agent messages have correct structure."""
        from agents.base import AgentMessage
        
        # Create test message
        message = AgentMessage(
            agent_id="test_agent",
            message_type="test_message",
            timestamp=datetime.now(),
            data={"test": "data"},
            metadata={"version": "1.0"}
        )
        
        # Check required fields
        self.assertEqual(message.agent_id, "test_agent")
        self.assertEqual(message.message_type, "test_message")
        self.assertIsInstance(message.timestamp, datetime)
        self.assertEqual(message.data, {"test": "data"})
        self.assertEqual(message.metadata, {"version": "1.0"})
        self.assertIsNotNone(message.message_id)
    
    def test_execution_context(self):
        """Test execution context management."""
        from agents.base import AgentExecutionContext, AgentMessage
        
        context = AgentExecutionContext(
            execution_id="test_context",
            config={"test": "config"},
            shared_data={"shared": "data"},
            messages=[]
        )
        
        # Test adding messages
        message = AgentMessage(
            agent_id="test_agent",
            message_type="test",
            timestamp=datetime.now(),
            data={}
        )
        
        context.messages.append(message)
        
        self.assertEqual(len(context.messages), 1)
        self.assertEqual(context.messages[0].agent_id, "test_agent")

if __name__ == "__main__":
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add integration tests
    suite.addTest(unittest.makeSuite(TestAgentIntegration))
    suite.addTest(unittest.makeSuite(TestAgentCommunication))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)