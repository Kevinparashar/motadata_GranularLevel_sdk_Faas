"""
Model Configuration

Configuration classes for ML models.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """
    Configuration for ML models.
    
    Provides a structured way to configure models with type,
    hyperparameters, and metadata.
    """
    
    model_type: str
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    model_id: Optional[str] = None
    version: str = "1.0.0"
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.model_type:
            raise ValueError("model_type is required")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Configuration as dictionary
        """
        return {
            'model_type': self.model_type,
            'hyperparameters': self.hyperparameters,
            'metadata': self.metadata,
            'model_id': self.model_id,
            'version': self.version
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ModelConfig':
        """
        Create configuration from dictionary.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            ModelConfig instance
        """
        return cls(
            model_type=config_dict.get('model_type'),
            hyperparameters=config_dict.get('hyperparameters', {}),
            metadata=config_dict.get('metadata', {}),
            model_id=config_dict.get('model_id'),
            version=config_dict.get('version', '1.0.0')
        )
    
    def update_hyperparameters(self, **kwargs) -> None:
        """
        Update hyperparameters.
        
        Args:
            **kwargs: Hyperparameters to update
        """
        self.hyperparameters.update(kwargs)
    
    def get_hyperparameter(self, key: str, default: Any = None) -> Any:
        """
        Get a hyperparameter value.
        
        Args:
            key: Hyperparameter key
            default: Default value if not found
            
        Returns:
            Hyperparameter value
        """
        return self.hyperparameters.get(key, default)


