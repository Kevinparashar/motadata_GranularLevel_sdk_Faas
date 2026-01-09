"""
Model Monitoring

Monitors model performance in production.
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ModelMonitoring:
    """
    Monitors model performance in production.
    
    Tracks performance metrics, prediction latency, error rates,
    and resource usage with alerting capabilities.
    """
    
    def __init__(
        self,
        tenant_id: Optional[str] = None
    ):
        """
        Initialize model monitoring.
        
        Args:
            tenant_id: Optional tenant ID
        """
        self.tenant_id = tenant_id
        self._metrics: Dict[str, List[Dict[str, Any]]] = {}
        
        logger.info(f"ModelMonitoring initialized for tenant: {tenant_id}")
    
    def track_prediction(
        self,
        model_id: str,
        prediction_time: float,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """
        Track a prediction.
        
        Args:
            model_id: Model ID
            prediction_time: Prediction latency in seconds
            success: Whether prediction succeeded
            error: Optional error message
        """
        metric = {
            'timestamp': datetime.utcnow(),
            'prediction_time': prediction_time,
            'success': success,
            'error': error
        }
        
        if model_id not in self._metrics:
            self._metrics[model_id] = []
        
        self._metrics[model_id].append(metric)
        logger.debug(f"Prediction tracked for {model_id}")
    
    def get_metrics(
        self,
        model_id: str,
        time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Args:
            model_id: Model ID
            time_window: Optional time window for metrics
            
        Returns:
            Performance metrics
        """
        if model_id not in self._metrics:
            return {}
        
        metrics = self._metrics[model_id]
        
        if time_window:
            cutoff = datetime.utcnow() - time_window
            metrics = [m for m in metrics if m['timestamp'] > cutoff]
        
        if not metrics:
            return {}
        
        success_count = sum(1 for m in metrics if m['success'])
        total_count = len(metrics)
        avg_latency = sum(m['prediction_time'] for m in metrics) / total_count
        
        return {
            'total_predictions': total_count,
            'success_rate': success_count / total_count if total_count > 0 else 0,
            'error_rate': 1 - (success_count / total_count) if total_count > 0 else 0,
            'avg_latency': avg_latency
        }
    
    def check_health(self, model_id: str) -> Dict[str, Any]:
        """
        Check model health.
        
        Args:
            model_id: Model ID
            
        Returns:
            Health status
        """
        metrics = self.get_metrics(model_id, timedelta(hours=1))
        
        if not metrics:
            return {'status': 'unknown', 'message': 'No recent metrics'}
        
        if metrics['error_rate'] > 0.1:
            return {'status': 'unhealthy', 'message': 'High error rate'}
        
        if metrics['avg_latency'] > 5.0:
            return {'status': 'degraded', 'message': 'High latency'}
        
        return {'status': 'healthy'}


