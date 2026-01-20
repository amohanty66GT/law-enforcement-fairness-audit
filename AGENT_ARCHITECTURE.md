# Agent-Based Architecture Documentation

## Overview

The Law Enforcement Fairness & Bias Audit system has been refactored from a monolithic architecture to a modular agent-based system. This document describes the architecture, benefits, and usage of the new system.

## Architecture Principles

### Single Responsibility
Each agent has one clear responsibility and operates independently:
- **Ingestion Agent**: Data fetching and normalization
- **Validation Agent**: Data quality and drift detection
- **Classification Agents**: Weapon and crime categorization
- **Analysis Agents**: Statistical and trend analysis
- **Reporting Agent**: Visualization and report generation

### Structured Communication
Agents communicate via structured data objects, not chat:
- **AgentMessage**: Standardized message format with metadata
- **Typed Data**: Validation results, classification results, statistical results
- **Execution Context**: Shared state and configuration

### Deterministic Operation
All agents operate deterministically unless explicitly designed otherwise:
- **Reproducible Results**: Same input produces same output
- **Transparent Logging**: All decisions and operations logged
- **Error Handling**: Graceful degradation with detailed error reporting

## Agent Specifications

### 1. Ingestion Agent (`IngestionAgent`)

**Responsibility**: Fetch and normalize data from external sources

**Input**: Configuration (data source, pagination settings)
**Output**: List of normalized records

**Features**:
- FBI Wanted API integration with pagination
- Deduplication based on record UIDs
- Rate limiting and retry logic
- Incremental updates support

**Configuration**:
```json
{
  "max_retries": 3,
  "timeout_seconds": 30,
  "batch_size": 100
}
```

### 2. Validation & Drift Agent (`ValidationDriftAgent`)

**Responsibility**: Validate data quality and detect distribution changes

**Input**: Raw data records
**Output**: Validation report with quality metrics

**Features**:
- Schema validation (required fields, data types)
- Missing data analysis
- Distribution drift detection
- Quality score calculation

**Configuration**:
```json
{
  "missing_threshold": 0.5,
  "drift_detection_window": 30,
  "quality_score_threshold": 0.7
}
```

### 3. Weapon Classification Agent (`WeaponClassificationAgent`)

**Responsibility**: Categorize weapon information from text descriptions

**Input**: Records with text descriptions
**Output**: Records with weapon categories and confidence scores

**Categories**: `firearm`, `knife`, `blunt_object`, `none`, `unknown`, `other`

**Features**:
- Rule-based text classification
- Confidence scoring
- Fallback handling for ambiguous cases
- Detailed classification metadata

**Configuration**:
```json
{
  "confidence_threshold": 0.8,
  "unknown_threshold": 0.3
}
```

### 4. Serious Crime Filter Agent (`SeriousCrimeFilterAgent`)

**Responsibility**: Identify and flag serious crimes consistently

**Input**: Records with crime descriptions
**Output**: Records with severity flags

**Serious Crime Types**:
- Homicide/Murder
- Aggravated Assault
- Robbery
- Kidnapping
- Rape/Sexual Assault
- Terrorism

**Configuration**:
```json
{
  "crime_keywords": [
    "homicide", "murder", "aggravated assault", 
    "robbery", "kidnapping", "rape", "terrorism"
  ]
}
```

### 5. Statistical Analysis Agent (`StatisticalAnalysisAgent`)

**Responsibility**: Perform statistical bias detection tests

**Input**: Processed records with classifications
**Output**: Statistical test results with p-values and effect sizes

**Tests Performed**:
- Chi-square tests for distribution analysis
- Association tests between variables
- Effect size calculations (Cramér's V)
- Significance interpretation

**Configuration**:
```json
{
  "confidence_level": 0.95,
  "min_sample_size": 30,
  "effect_size_threshold": 0.1
}
```

### 6. Trend & Anomaly Agent (`TrendAnomalyAgent`)

**Responsibility**: Analyze temporal patterns and detect anomalies

**Input**: Time-series data
**Output**: Trend analysis and anomaly detection results

**Features**:
- Linear trend analysis
- Seasonal decomposition
- Anomaly detection using statistical methods
- Change point detection

**Configuration**:
```json
{
  "window_size": 12,
  "anomaly_threshold": 2.0,
  "min_periods": 6
}
```

### 7. Reporting & Visualization Agent (`ReportingVisualizationAgent`)

**Responsibility**: Generate privacy-compliant reports and visualizations

**Input**: All agent outputs
**Output**: Comprehensive report with charts and metrics

**Features**:
- Aggregation threshold enforcement
- Privacy-compliant visualizations
- Executive summary generation
- Multi-format output (JSON, Markdown)

**Configuration**:
```json
{
  "min_aggregation_threshold": 5,
  "max_categories_display": 10
}
```

## Orchestrator

The `AgentOrchestrator` manages the execution pipeline:

### Features
- **Sequential Execution**: Runs agents in correct dependency order
- **Error Handling**: Continues pipeline on non-critical failures
- **Result Aggregation**: Collects and structures all agent outputs
- **Execution Logging**: Detailed performance and error tracking
- **Configuration Validation**: Validates pipeline configuration before execution

### Pipeline Flow
```
1. Ingestion Agent → Raw Data
2. Validation Agent → Quality Report
3. Weapon Classification Agent → Classified Data
4. Serious Crime Agent → Processed Data
5. Statistical Analysis Agent → Statistical Results
6. Trend Analysis Agent → Trend Results
7. Reporting Agent → Final Report
```

## Usage Examples

### Basic Execution
```python
from agents.orchestrator import AgentOrchestrator

# Initialize with configuration
orchestrator = AgentOrchestrator(agent_config)

# Execute pipeline
result = orchestrator.execute_pipeline(pipeline_config)

# Check results
if result["status"] == "success":
    print(f"Pipeline completed: {result['execution_id']}")
else:
    print(f"Pipeline failed: {result['error']}")
```

### Command Line Usage
```bash
# Run with default configuration
python scripts/run_agent_analysis.py --data-source sample

# Run with custom parameters
python scripts/run_agent_analysis.py \
  --data-source fbi \
  --max-pages 20 \
  --confidence-level 0.99 \
  --min-sample-size 50 \
  --output-dir results

# Compare approaches
python scripts/run_analysis_comparison.py --approach both
```

### Configuration File
```json
{
  "ingestion": {
    "max_retries": 3,
    "timeout_seconds": 30
  },
  "validation": {
    "missing_threshold": 0.5,
    "quality_score_threshold": 0.7
  },
  "statistical": {
    "confidence_level": 0.95,
    "min_sample_size": 30
  },
  "reporting": {
    "min_aggregation_threshold": 5
  }
}
```

## Benefits Over Monolithic Architecture

### Resilience
- **Graceful Degradation**: System continues if individual agents fail
- **Error Isolation**: Failures don't cascade through entire system
- **Recovery Options**: Failed agents can be retried independently

### Modularity
- **Independent Testing**: Each agent can be unit tested
- **Parallel Development**: Teams can work on different agents simultaneously
- **Easy Replacement**: Agents can be swapped without affecting others

### Transparency
- **Detailed Logging**: Every agent operation is logged
- **Performance Metrics**: Execution time and resource usage per agent
- **Decision Tracking**: All classification and analysis decisions recorded

### Extensibility
- **New Agents**: Easy to add new analysis capabilities
- **Configuration**: Runtime configuration without code changes
- **Plugin Architecture**: Agents can be loaded dynamically

### Maintainability
- **Single Responsibility**: Each agent has clear, focused purpose
- **Loose Coupling**: Minimal dependencies between agents
- **Clear Interfaces**: Standardized input/output contracts

## Testing

### Unit Tests
Each agent includes comprehensive unit tests:
```python
def test_weapon_classification_agent():
    agent = WeaponClassificationAgent()
    result = agent.execute(context, sample_data)
    assert result.message_type == "weapon_classified_data"
    assert len(result.data) == len(sample_data)
```

### Integration Tests
Full pipeline testing with realistic data:
```python
def test_complete_pipeline():
    orchestrator = AgentOrchestrator(test_config)
    result = orchestrator.execute_pipeline(pipeline_config)
    assert result["status"] == "success"
    assert len(result["results"]) == 7  # All agents
```

### Performance Tests
Execution time and resource usage validation:
```python
def test_pipeline_performance():
    start_time = time.time()
    result = orchestrator.execute_pipeline(config)
    duration = time.time() - start_time
    assert duration < 60  # Should complete within 1 minute
```

## Error Handling

### Agent-Level Errors
- **Validation Errors**: Input data doesn't meet requirements
- **Processing Errors**: Agent-specific failures (API timeouts, etc.)
- **Configuration Errors**: Invalid agent configuration

### Pipeline-Level Errors
- **Critical Failures**: Stop entire pipeline (e.g., no data ingested)
- **Non-Critical Failures**: Continue with remaining agents
- **Cascading Failures**: Handle dependencies between agents

### Error Recovery
- **Retry Logic**: Automatic retries for transient failures
- **Fallback Options**: Alternative processing paths
- **Graceful Degradation**: Partial results when possible

## Future Enhancements

### Parallel Execution
Run independent agents concurrently for better performance:
```python
# Future capability
orchestrator.execute_parallel(["weapon_classification", "validation"])
```

### Dynamic Configuration
Update agent configuration at runtime:
```python
# Future capability
orchestrator.update_agent_config("statistical", new_config)
```

### Agent Marketplace
Plugin system for community-contributed agents:
```python
# Future capability
orchestrator.load_plugin("custom_bias_detector")
```

### Real-Time Monitoring
Live dashboard for agent execution:
- Agent health status
- Performance metrics
- Error rates and trends
- Resource utilization

## Conclusion

The agent-based architecture provides a robust, scalable, and maintainable foundation for law enforcement data analysis. It enables:

- **Better Error Handling**: System resilience and recovery
- **Improved Testing**: Comprehensive unit and integration tests
- **Enhanced Transparency**: Complete visibility into processing
- **Easy Extension**: Simple addition of new analysis capabilities
- **Ethical Compliance**: Built-in privacy protection and aggregation

This architecture positions the system for future enhancements while maintaining the highest standards of ethical data analysis.