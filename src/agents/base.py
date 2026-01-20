"""
Base agent framework for the crime data analysis system.
Defines the core agent interface and data structures.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)

@dataclass
class AgentMessage:
    """Structured data object for agent communication."""
    agent_id: str
    message_type: str
    timestamp: datetime
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class ValidationResult:
    """Result of data validation operations."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ClassificationResult:
    """Result of classification operations."""
    category: str
    confidence: float
    raw_input: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StatisticalResult:
    """Result of statistical analysis."""
    test_name: str
    statistic: float
    p_value: float
    effect_size: Optional[float]
    interpretation: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TrendResult:
    """Result of trend analysis."""
    trend_type: str
    direction: str
    significance: float
    anomalies: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentExecutionContext:
    """Context for agent execution with shared state."""
    execution_id: str
    config: Dict[str, Any]
    shared_data: Dict[str, Any] = field(default_factory=dict)
    messages: List[AgentMessage] = field(default_factory=list)

class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.logger = logging.getLogger(f"agent.{agent_id}")
        
    @abstractmethod
    def execute(self, context: AgentExecutionContext, input_data: Any) -> AgentMessage:
        """Execute the agent's primary function."""
        pass
    
    def validate_input(self, input_data: Any) -> ValidationResult:
        """Validate input data. Override in subclasses for specific validation."""
        return ValidationResult(is_valid=True)
    
    def create_message(self, message_type: str, data: Any, metadata: Optional[Dict] = None) -> AgentMessage:
        """Create a structured message for communication."""
        return AgentMessage(
            agent_id=self.agent_id,
            message_type=message_type,
            timestamp=datetime.now(),
            data=data,
            metadata=metadata or {}
        )
    
    def log_execution(self, action: str, details: Optional[Dict] = None):
        """Log agent execution for transparency."""
        log_data = {
            'agent_id': self.agent_id,
            'action': action,
            'timestamp': datetime.now().isoformat()
        }
        if details:
            log_data.update(details)
        
        self.logger.info(f"Agent {self.agent_id}: {action}", extra=log_data)

class AgentError(Exception):
    """Base exception for agent-related errors."""
    
    def __init__(self, agent_id: str, message: str, details: Optional[Dict] = None):
        self.agent_id = agent_id
        self.details = details or {}
        super().__init__(f"Agent {agent_id}: {message}")

class ValidationError(AgentError):
    """Exception for validation failures."""
    pass

class ProcessingError(AgentError):
    """Exception for processing failures."""
    pass