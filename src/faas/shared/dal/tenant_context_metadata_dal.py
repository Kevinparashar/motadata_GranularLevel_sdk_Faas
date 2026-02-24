"""
Data Access Layer for Tenant Context Metadata.

Abstracts all database operations for tenant context metadata and activity history persistence.
Tables are assumed to exist (managed by migrations/DAL).
"""


import json
import logging
from typing import Any, Dict, List, Optional

from src.core.postgresql_database import DatabaseConnection

logger = logging.getLogger(__name__)


class TenantContextMetadataDAL:
    """Data Access Layer for tenant context metadata and activity persistence."""

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize TenantContextMetadataDAL.

        Args:
            db_connection: Database connection instance.
        """
        self.db = db_connection

    async def save_tenant_metadata(
        self,
        tenant_id: str,
        tenant_tier: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Save or update tenant context metadata.

        Args:
            tenant_id: Tenant identifier.
            tenant_tier: Optional tenant tier.
            configuration: Optional tenant-specific configuration.
            metadata: Optional metadata.

        Returns:
            Tenant ID.
        """
        result = await self.db.execute_query(
            """
            INSERT INTO tenant_context_metadata (
                tenant_id, tenant_tier, configuration, metadata, created_at, updated_at
            ) VALUES (
                $1, $2, $3::jsonb, $4::jsonb, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            ON CONFLICT (tenant_id) DO UPDATE SET
                tenant_tier = EXCLUDED.tenant_tier,
                configuration = EXCLUDED.configuration,
                metadata = EXCLUDED.metadata,
                updated_at = CURRENT_TIMESTAMP
            RETURNING tenant_id;
            """,
            params=(
                tenant_id,
                tenant_tier,
                json.dumps(configuration) if configuration else None,
                json.dumps(metadata or {}),
            ),
            fetch_one=True,
        )
        return str(result["tenant_id"]) if result else tenant_id

    async def get_tenant_metadata(
        self,
        tenant_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get tenant context metadata.

        Args:
            tenant_id: Tenant identifier.

        Returns:
            Tenant metadata record or None.
        """
        result = await self.db.execute_query(
            """
            SELECT 
                tenant_id, tenant_tier, configuration, metadata, created_at, updated_at
            FROM tenant_context_metadata
            WHERE tenant_id = $1
            """,
            params=(tenant_id,),
            fetch_one=True,
        )

        if result:
            if result.get("configuration"):
                result["configuration"] = (
                    json.loads(result["configuration"])
                    if isinstance(result["configuration"], str)
                    else result["configuration"]
                )
            if result.get("metadata"):
                result["metadata"] = (
                    json.loads(result["metadata"])
                    if isinstance(result["metadata"], str)
                    else result["metadata"]
                )
        return result

    async def save_tenant_activity(
        self,
        tenant_id: str,
        activity_type: str,  # "request", "operation", "config_change", etc.
        activity_description: Optional[str] = None,
        component: Optional[str] = None,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        activity_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Save tenant activity to history.

        Args:
            tenant_id: Tenant identifier.
            activity_type: Type of activity.
            activity_description: Optional activity description.
            component: Optional component name (e.g., "rag", "gateway").
            user_id: Optional user identifier.
            correlation_id: Optional correlation ID.
            activity_data: Optional activity-specific data.
            metadata: Optional metadata.

        Returns:
            Activity record ID.
        """
        import uuid
        activity_id = f"tenant_activity_{uuid.uuid4().hex[:16]}"

        result = await self.db.execute_query(
            """
            INSERT INTO tenant_activity_history (
                activity_id, tenant_id, activity_type, activity_description,
                component, user_id, correlation_id, activity_data, metadata, created_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9::jsonb, CURRENT_TIMESTAMP
            )
            RETURNING activity_id;
            """,
            params=(
                activity_id,
                tenant_id,
                activity_type,
                activity_description,
                component,
                user_id,
                correlation_id,
                json.dumps(activity_data) if activity_data else None,
                json.dumps(metadata or {}),
            ),
            fetch_one=True,
        )
        return str(result["activity_id"]) if result else activity_id

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
            tenant_id: Tenant identifier.
            activity_type: Optional activity type filter.
            component: Optional component filter.
            user_id: Optional user identifier filter.
            limit: Maximum number of records to return.
            offset: Offset for pagination.

        Returns:
            List of activity history records.
        """
        query = """
        SELECT 
            activity_id, tenant_id, activity_type, activity_description,
            component, user_id, correlation_id, activity_data, metadata, created_at
        FROM tenant_activity_history
        WHERE tenant_id = $1
        """
        params: List[Any] = [tenant_id]
        param_count = 1

        if activity_type:
            param_count += 1
            query += f" AND activity_type = ${param_count}"
            params.append(activity_type)
        if component:
            param_count += 1
            query += f" AND component = ${param_count}"
            params.append(component)
        if user_id:
            param_count += 1
            query += f" AND user_id = ${param_count}"
            params.append(user_id)

        query += f" ORDER BY created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
        params.extend([limit, offset])

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        if results:
            for record in results:
                if record.get("activity_data"):
                    record["activity_data"] = (
                        json.loads(record["activity_data"])
                        if isinstance(record["activity_data"], str)
                        else record["activity_data"]
                    )
                if record.get("metadata"):
                    record["metadata"] = (
                        json.loads(record["metadata"])
                        if isinstance(record["metadata"], str)
                        else record["metadata"]
                    )
        return results if results else []

    async def get_tenant_configuration(
        self,
        tenant_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get tenant-specific configuration.

        Args:
            tenant_id: Tenant identifier.

        Returns:
            Tenant configuration dictionary or None.
        """
        metadata = await self.get_tenant_metadata(tenant_id)
        if metadata and metadata.get("configuration"):
            return metadata["configuration"]
        return None

    async def update_tenant_configuration(
        self,
        tenant_id: str,
        configuration: Dict[str, Any],
    ) -> bool:
        """
        Update tenant-specific configuration.

        Args:
            tenant_id: Tenant identifier.
            configuration: Configuration dictionary to update.

        Returns:
            True if successful.
        """
        # Get existing metadata
        existing = await self.get_tenant_metadata(tenant_id)
        existing_config = existing.get("configuration", {}) if existing else {}
        
        # Merge configurations
        merged_config = {**existing_config, **configuration}
        
        # Save updated metadata
        await self.save_tenant_metadata(
            tenant_id=tenant_id,
            tenant_tier=existing.get("tenant_tier") if existing else None,
            configuration=merged_config,
            metadata=existing.get("metadata") if existing else None,
        )
        
        return True

    async def get_tenant_tier(
        self,
        tenant_id: str,
    ) -> Optional[str]:
        """
        Get tenant tier from metadata.

        Args:
            tenant_id: Tenant identifier.

        Returns:
            Tenant tier or None.
        """
        metadata = await self.get_tenant_metadata(tenant_id)
        if metadata:
            return metadata.get("tenant_tier")
        return None

    async def set_tenant_tier(
        self,
        tenant_id: str,
        tenant_tier: str,
    ) -> bool:
        """
        Set tenant tier in metadata.

        Args:
            tenant_id: Tenant identifier.
            tenant_tier: Tenant tier.

        Returns:
            True if successful.
        """
        # Get existing metadata
        existing = await self.get_tenant_metadata(tenant_id)
        
        # Save with updated tier
        await self.save_tenant_metadata(
            tenant_id=tenant_id,
            tenant_tier=tenant_tier,
            configuration=existing.get("configuration") if existing else None,
            metadata=existing.get("metadata") if existing else None,
        )
        
        return True

    async def get_tenant_activity_stats(
        self,
        tenant_id: str,
        time_range_hours: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get tenant activity statistics.

        Args:
            tenant_id: Tenant identifier.
            time_range_hours: Optional time range in hours.

        Returns:
            Dictionary with activity statistics.
        """
        query = """
        SELECT 
            COUNT(*) as total_activities,
            COUNT(DISTINCT activity_type) as unique_activity_types,
            COUNT(DISTINCT component) as unique_components,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(DISTINCT correlation_id) as unique_correlations
        FROM tenant_activity_history
        WHERE tenant_id = $1
        """
        params: List[Any] = [tenant_id]

        if time_range_hours:
            query += " AND created_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour' * $2"
            params.append(time_range_hours)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_one=True,
        )

        if result:
            return {
                "total_activities": result.get("total_activities", 0) or 0,
                "unique_activity_types": result.get("unique_activity_types", 0) or 0,
                "unique_components": result.get("unique_components", 0) or 0,
                "unique_users": result.get("unique_users", 0) or 0,
                "unique_correlations": result.get("unique_correlations", 0) or 0,
            }
        return {
            "total_activities": 0,
            "unique_activity_types": 0,
            "unique_components": 0,
            "unique_users": 0,
            "unique_correlations": 0,
        }

    async def get_tenant_component_activity(
        self,
        tenant_id: str,
        component: str,
        time_range_hours: Optional[int] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get tenant activity for a specific component.

        Args:
            tenant_id: Tenant identifier.
            component: Component name.
            time_range_hours: Optional time range in hours.
            limit: Maximum number of records to return.

        Returns:
            List of activity records for the component.
        """
        query = """
        SELECT 
            activity_id, tenant_id, activity_type, activity_description,
            component, user_id, correlation_id, activity_data, metadata, created_at
        FROM tenant_activity_history
        WHERE tenant_id = $1 AND component = $2
        """
        params: List[Any] = [tenant_id, component]

        if time_range_hours:
            query += " AND created_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour' * $3"
            params.append(time_range_hours)
            query += f" ORDER BY created_at DESC LIMIT $4"
            params.append(limit)
        else:
            query += f" ORDER BY created_at DESC LIMIT $3"
            params.append(limit)

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        if results:
            for record in results:
                if record.get("activity_data"):
                    record["activity_data"] = (
                        json.loads(record["activity_data"])
                        if isinstance(record["activity_data"], str)
                        else record["activity_data"]
                    )
                if record.get("metadata"):
                    record["metadata"] = (
                        json.loads(record["metadata"])
                        if isinstance(record["metadata"], str)
                        else record["metadata"]
                    )
        return results if results else []

    async def list_tenants(
        self,
        tenant_tier: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List tenants with metadata.

        Args:
            tenant_tier: Optional tier filter.
            limit: Maximum number of records to return.
            offset: Offset for pagination.

        Returns:
            List of tenant metadata records.
        """
        query = """
        SELECT 
            tenant_id, tenant_tier, configuration, metadata, created_at, updated_at
        FROM tenant_context_metadata
        WHERE 1=1
        """
        params: List[Any] = []
        param_count = 0

        if tenant_tier:
            param_count += 1
            query += f" AND tenant_tier = ${param_count}"
            params.append(tenant_tier)

        query += f" ORDER BY updated_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
        params.extend([limit, offset])

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        if results:
            for record in results:
                if record.get("configuration"):
                    record["configuration"] = (
                        json.loads(record["configuration"])
                        if isinstance(record["configuration"], str)
                        else record["configuration"]
                    )
                if record.get("metadata"):
                    record["metadata"] = (
                        json.loads(record["metadata"])
                        if isinstance(record["metadata"], str)
                        else record["metadata"]
                    )
        return results if results else []

    async def cleanup_old_activity(
        self,
        days: int = 90,
        tenant_id: Optional[str] = None,
    ) -> int:
        """
        Clean up old tenant activity records.

        Args:
            days: Number of days to keep (delete older records).
            tenant_id: Optional tenant identifier.

        Returns:
            Number of records deleted.
        """
        query = """
        DELETE FROM tenant_activity_history
        WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
        """ % days
        params: List[Any] = []
        if tenant_id:
            query = query.replace("WHERE", "WHERE tenant_id = $1 AND")
            params.append(tenant_id)

        result = await self.db.execute_query(
            query,
            params=tuple(params) if params else None,
            fetch_all=False,
        )
        return result if result else 0

