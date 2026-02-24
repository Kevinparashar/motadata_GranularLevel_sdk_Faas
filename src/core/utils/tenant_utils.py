"""
Tenant Utilities

Helper functions for tenant context management including tier determination.
"""

import logging
from typing import Optional, Dict, Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.faas.shared.dal.tenant_context_metadata_dal import TenantContextMetadataDAL

logger = logging.getLogger(__name__)

# Default tenant tier mapping (can be overridden)
_DEFAULT_TENANT_TIER_MAP: Dict[str, str] = {}


def get_tenant_tier(tenant_id: Optional[str], tier_map: Optional[Dict[str, str]] = None) -> Optional[str]:
    """
    Get tenant tier for a given tenant ID.
    
    Determines tenant tier from:
    1. Provided tier_map (highest priority)
    2. Default tier map
    3. Returns None if not found
    
    Args:
        tenant_id: Tenant identifier
        tier_map: Optional custom tier mapping (tenant_id -> tier)
        
    Returns:
        Tenant tier ("basic", "standard", "premium") or None
        
    Example:
        >>> get_tenant_tier("abc-123", {"abc-123": "premium"})
        'premium'
        >>> get_tenant_tier("unknown")
        None
    """
    if not tenant_id:
        return None
    
    # Check provided tier map first
    if tier_map and tenant_id in tier_map:
        return tier_map[tenant_id]
    
    # Check default tier map
    if tenant_id in _DEFAULT_TENANT_TIER_MAP:
        return _DEFAULT_TENANT_TIER_MAP[tenant_id]
    
    return None


async def get_tenant_tier_async(
    tenant_id: Optional[str],
    tenant_context_dal: Optional["TenantContextMetadataDAL"] = None,
    tier_map: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """
    Get tenant tier for a given tenant ID (async version with DAL support).
    
    Determines tenant tier from:
    1. Provided tier_map (highest priority)
    2. DAL metadata (if available)
    3. Default tier map
    4. Returns None if not found
    
    Args:
        tenant_id: Tenant identifier
        tenant_context_dal: Optional TenantContextMetadataDAL instance
        tier_map: Optional custom tier mapping (tenant_id -> tier)
        
    Returns:
        Tenant tier ("basic", "standard", "premium") or None
    """
    if not tenant_id:
        return None
    
    # Check provided tier map first
    if tier_map and tenant_id in tier_map:
        return tier_map[tenant_id]
    
    # Check DAL if available
    if tenant_context_dal:
        try:
            tier = await tenant_context_dal.get_tenant_tier(tenant_id)
            if tier:
                return tier
        except Exception as e:
            logger.debug(f"Failed to get tenant tier from DAL: {e}")
    
    # Check default tier map
    if tenant_id in _DEFAULT_TENANT_TIER_MAP:
        return _DEFAULT_TENANT_TIER_MAP[tenant_id]
    
    return None


def set_tenant_tier_mapping(tenant_id: str, tier: str) -> None:
    """
    Set tenant tier in default mapping.
    
    Args:
        tenant_id: Tenant identifier
        tier: Tenant tier ("basic", "standard", "premium")
        
    Example:
        >>> set_tenant_tier_mapping("abc-123", "premium")
    """
    if tenant_id and tier:
        _DEFAULT_TENANT_TIER_MAP[tenant_id] = tier


async def set_tenant_tier_mapping_async(
    tenant_id: str,
    tier: str,
    tenant_context_dal: Optional["TenantContextMetadataDAL"] = None,
    component: Optional[str] = None,
    user_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> None:
    """
    Set tenant tier in default mapping and persist to DAL if available (async version).
    
    Args:
        tenant_id: Tenant identifier
        tier: Tenant tier ("basic", "standard", "premium")
        tenant_context_dal: Optional TenantContextMetadataDAL instance
        component: Optional component name for activity tracking
        user_id: Optional user identifier for activity tracking
        correlation_id: Optional correlation ID for activity tracking
        
    Example:
        >>> await set_tenant_tier_mapping_async("abc-123", "premium", dal)
    """
    if tenant_id and tier:
        _DEFAULT_TENANT_TIER_MAP[tenant_id] = tier
        
        # Persist to DAL if available
        if tenant_context_dal:
            try:
                await tenant_context_dal.set_tenant_tier(tenant_id, tier)
                # Track activity
                await tenant_context_dal.save_tenant_activity(
                    tenant_id=tenant_id,
                    activity_type="config_change",
                    activity_description=f"Tenant tier set to {tier}",
                    component=component or "tenant_utils",
                    user_id=user_id,
                    correlation_id=correlation_id,
                    activity_data={"tier": tier},
                )
            except Exception as e:
                logger.debug(f"Failed to persist tenant tier to DAL: {e}")


def set_tenant_tier_mappings(mappings: Dict[str, str]) -> None:
    """
    Set multiple tenant tier mappings at once.
    
    Args:
        mappings: Dictionary mapping tenant_id to tier
        
    Example:
        >>> set_tenant_tier_mappings({"abc-123": "premium", "def-456": "standard"})
    """
    if mappings:
        _DEFAULT_TENANT_TIER_MAP.update(mappings)


async def set_tenant_tier_mappings_async(
    mappings: Dict[str, str],
    tenant_context_dal: Optional["TenantContextMetadataDAL"] = None,
    component: Optional[str] = None,
    user_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> None:
    """
    Set multiple tenant tier mappings at once and persist to DAL if available (async version).
    
    Args:
        mappings: Dictionary mapping tenant_id to tier
        tenant_context_dal: Optional TenantContextMetadataDAL instance
        component: Optional component name for activity tracking
        user_id: Optional user identifier for activity tracking
        correlation_id: Optional correlation ID for activity tracking
        
    Example:
        >>> await set_tenant_tier_mappings_async({"abc-123": "premium"}, dal)
    """
    if mappings:
        _DEFAULT_TENANT_TIER_MAP.update(mappings)
        
        # Persist to DAL if available
        if tenant_context_dal:
            try:
                for tenant_id, tier in mappings.items():
                    await tenant_context_dal.set_tenant_tier(tenant_id, tier)
                    # Track activity
                    await tenant_context_dal.save_tenant_activity(
                        tenant_id=tenant_id,
                        activity_type="config_change",
                        activity_description=f"Tenant tier set to {tier}",
                        component=component or "tenant_utils",
                        user_id=user_id,
                        correlation_id=correlation_id,
                        activity_data={"tier": tier},
                    )
            except Exception as e:
                logger.debug(f"Failed to persist tenant tier mappings to DAL: {e}")


def clear_tenant_tier_mappings() -> None:
    """Clear all tenant tier mappings."""
    _DEFAULT_TENANT_TIER_MAP.clear()


def get_tenant_tier_mappings() -> Dict[str, str]:
    """
    Get current tenant tier mappings.
    
    Returns:
        Dictionary of tenant_id -> tier mappings
    """
    return _DEFAULT_TENANT_TIER_MAP.copy()


class TenantContextManager:
    """
    Manager for tenant context with DAL integration.
    
    Provides methods to manage tenant metadata, configuration, and activity history
    with optional persistence via TenantContextMetadataDAL.
    """
    
    def __init__(self, tenant_context_dal: Optional["TenantContextMetadataDAL"] = None):
        """
        Initialize TenantContextManager.
        
        Args:
            tenant_context_dal: Optional TenantContextMetadataDAL instance
        """
        self.tenant_context_dal = tenant_context_dal
    
    async def track_tenant_activity(
        self,
        tenant_id: str,
        activity_type: str,
        activity_description: Optional[str] = None,
        component: Optional[str] = None,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        activity_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Track tenant activity.
        
        Args:
            tenant_id: Tenant identifier
            activity_type: Type of activity
            activity_description: Optional activity description
            component: Optional component name
            user_id: Optional user identifier
            correlation_id: Optional correlation ID
            activity_data: Optional activity-specific data
            metadata: Optional metadata
            
        Returns:
            Activity ID if DAL is available, None otherwise
        """
        if not self.tenant_context_dal:
            return None
        
        try:
            return await self.tenant_context_dal.save_tenant_activity(
                tenant_id=tenant_id,
                activity_type=activity_type,
                activity_description=activity_description,
                component=component,
                user_id=user_id,
                correlation_id=correlation_id,
                activity_data=activity_data,
                metadata=metadata,
            )
        except Exception as e:
            logger.debug(f"Failed to track tenant activity: {e}")
            return None
    
    async def get_tenant_metadata(
        self,
        tenant_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get tenant metadata.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Tenant metadata or None
        """
        if not self.tenant_context_dal:
            return None
        
        try:
            return await self.tenant_context_dal.get_tenant_metadata(tenant_id)
        except Exception as e:
            logger.debug(f"Failed to get tenant metadata: {e}")
            return None
    
    async def save_tenant_metadata(
        self,
        tenant_id: str,
        tenant_tier: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Save tenant metadata.
        
        Args:
            tenant_id: Tenant identifier
            tenant_tier: Optional tenant tier
            configuration: Optional tenant-specific configuration
            metadata: Optional metadata
            
        Returns:
            Tenant ID if successful, None otherwise
        """
        if not self.tenant_context_dal:
            return None
        
        try:
            return await self.tenant_context_dal.save_tenant_metadata(
                tenant_id=tenant_id,
                tenant_tier=tenant_tier,
                configuration=configuration,
                metadata=metadata,
            )
        except Exception as e:
            logger.debug(f"Failed to save tenant metadata: {e}")
            return None
    
    async def get_tenant_configuration(
        self,
        tenant_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get tenant-specific configuration.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Tenant configuration or None
        """
        if not self.tenant_context_dal:
            return None
        
        try:
            return await self.tenant_context_dal.get_tenant_configuration(tenant_id)
        except Exception as e:
            logger.debug(f"Failed to get tenant configuration: {e}")
            return None
    
    async def update_tenant_configuration(
        self,
        tenant_id: str,
        configuration: Dict[str, Any],
        component: Optional[str] = None,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> bool:
        """
        Update tenant-specific configuration.
        
        Args:
            tenant_id: Tenant identifier
            configuration: Configuration dictionary to update
            component: Optional component name for activity tracking
            user_id: Optional user identifier for activity tracking
            correlation_id: Optional correlation ID for activity tracking
            
        Returns:
            True if successful, False otherwise
        """
        if not self.tenant_context_dal:
            return False
        
        try:
            success = await self.tenant_context_dal.update_tenant_configuration(
                tenant_id, configuration
            )
            if success:
                # Track activity
                await self.track_tenant_activity(
                    tenant_id=tenant_id,
                    activity_type="config_change",
                    activity_description="Tenant configuration updated",
                    component=component or "tenant_utils",
                    user_id=user_id,
                    correlation_id=correlation_id,
                    activity_data={"configuration": configuration},
                )
            return success
        except Exception as e:
            logger.debug(f"Failed to update tenant configuration: {e}")
            return False
    
    async def get_tenant_activity_history(
        self,
        tenant_id: str,
        activity_type: Optional[str] = None,
        component: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get tenant activity history.
        
        Args:
            tenant_id: Tenant identifier
            activity_type: Optional activity type filter
            component: Optional component filter
            user_id: Optional user identifier filter
            limit: Maximum number of records to return
            offset: Offset for pagination
            
        Returns:
            List of activity history records
        """
        if not self.tenant_context_dal:
            return []
        
        try:
            return await self.tenant_context_dal.get_tenant_activity_history(
                tenant_id=tenant_id,
                activity_type=activity_type,
                component=component,
                user_id=user_id,
                limit=limit,
                offset=offset,
            )
        except Exception as e:
            logger.debug(f"Failed to get tenant activity history: {e}")
            return []
    
    async def get_tenant_activity_stats(
        self,
        tenant_id: str,
        time_range_hours: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get tenant activity statistics.
        
        Args:
            tenant_id: Tenant identifier
            time_range_hours: Optional time range in hours
            
        Returns:
            Dictionary with activity statistics
        """
        if not self.tenant_context_dal:
            return {
                "total_activities": 0,
                "unique_activity_types": 0,
                "unique_components": 0,
                "unique_users": 0,
                "unique_correlations": 0,
            }
        
        try:
            return await self.tenant_context_dal.get_tenant_activity_stats(
                tenant_id=tenant_id,
                time_range_hours=time_range_hours,
            )
        except Exception as e:
            logger.debug(f"Failed to get tenant activity stats: {e}")
            return {
                "total_activities": 0,
                "unique_activity_types": 0,
                "unique_components": 0,
                "unique_users": 0,
                "unique_correlations": 0,
            }


def add_tenant_attributes_to_span(
    span: Any,
    tenant_id: Optional[str],
    tenant_tier: Optional[str] = None,
    tier_map: Optional[Dict[str, str]] = None,
    attribute_prefix: str = "tenant",
) -> None:
    """
    Add tenant.id and tenant.tier attributes to an OTEL span.
    
    This is a convenience function to ensure consistent tenant attribute naming
    across all spans in the SDK.
    
    Args:
        span: OTEL span object (OTELSpan or OpenTelemetry span)
        tenant_id: Tenant identifier
        tenant_tier: Tenant tier (optional, will be looked up if not provided)
        tier_map: Optional custom tier mapping
        attribute_prefix: Prefix for attribute keys (default: "tenant")
        
    Example:
        >>> from src.core.otel_integration import OTELTracer
        >>> tracer = OTELTracer("test")
        >>> with tracer.start_trace("test") as span:
        ...     add_tenant_attributes_to_span(span, "abc-123", "premium")
    """
    if not span:
        return
    
    # Set tenant.id if provided
    if tenant_id:
        attr_key = f"{attribute_prefix}.id"
        if hasattr(span, "set_attribute"):
            span.set_attribute(attr_key, tenant_id)
        elif hasattr(span, "_span") and span._span:
            try:
                span._span.set_attribute(attr_key, tenant_id)
            except Exception:
                pass
    
    # Determine tenant tier if not provided
    if tenant_id and not tenant_tier:
        tenant_tier = get_tenant_tier(tenant_id, tier_map=tier_map)
    
    # Set tenant.tier if available
    if tenant_tier:
        tier_key = f"{attribute_prefix}.tier"
        if hasattr(span, "set_attribute"):
            span.set_attribute(tier_key, tenant_tier)
        elif hasattr(span, "_span") and span._span:
            try:
                span._span.set_attribute(tier_key, tenant_tier)
            except Exception:
                pass

