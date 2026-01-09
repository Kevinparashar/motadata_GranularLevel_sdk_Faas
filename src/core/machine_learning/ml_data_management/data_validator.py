"""
Data Validator

Validates data quality and schema.
"""

from typing import Dict, Any, Optional
import logging
import pandas as pd

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates data quality and schema."""
    
    def validate(
        self,
        data: Any,
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate data.
        
        Args:
            data: Data to validate
            schema: Optional schema
            
        Returns:
            Validation results
        """
        results = {
            'valid': True,
            'errors': []
        }
        
        if isinstance(data, pd.DataFrame):
            # Check for missing values
            missing = data.isnull().sum()
            if missing.any():
                results['errors'].append(f"Missing values: {missing.to_dict()}")
            
            # Check schema if provided
            if schema:
                for col, col_schema in schema.items():
                    if col not in data.columns:
                        results['errors'].append(f"Missing column: {col}")
        
        results['valid'] = len(results['errors']) == 0
        return results


