"""
Data Access Layer for Codec Context.

Abstracts all database operations for codec encoding/decoding history and schema context persistence.
Tables are assumed to exist (managed by migrations/DAL).
"""


import json
import logging
from typing import Any, Dict, List, Optional

from src.core.postgresql_database import DatabaseConnection

logger = logging.getLogger(__name__)


class CodecContextDAL:
    """Data Access Layer for codec context and serialization history persistence."""

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize CodecContextDAL.

        Args:
            db_connection: Database connection instance.
        """
        self.db = db_connection

    async def save_codec_operation(
        self,
        operation_id: str,
        operation_type: str,  # "encode", "decode"
        message_type: str,
        schema_version: str,
        codec_type: str = "json",
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        payload_size: Optional[int] = None,
        status: str = "success",  # "success", "error"
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
        migration_used: bool = False,
        source_version: Optional[str] = None,
        target_version: Optional[str] = None,
        validation_performed: bool = False,
        validation_passed: Optional[bool] = None,
        context_state: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Save codec operation to history.

        Args:
            operation_id: Unique operation identifier.
            operation_type: Operation type (encode, decode).
            message_type: Message type (e.g., "agent_message").
            schema_version: Schema version used.
            codec_type: Codec type (e.g., "json").
            tenant_id: Tenant identifier for tenant isolation.
            user_id: Optional user identifier.
            correlation_id: Optional correlation ID for request tracking.
            payload_size: Size of payload in bytes.
            status: Operation status (success, error).
            error_message: Optional error message.
            error_type: Optional error type.
            migration_used: Whether schema migration was used.
            source_version: Optional source schema version (for migrations).
            target_version: Optional target schema version (for migrations).
            validation_performed: Whether schema validation was performed.
            validation_passed: Whether validation passed.
            context_state: Optional serialization context state.
            metadata: Optional metadata.

        Returns:
            Operation record ID.
        """
        result = await self.db.execute_query(
            """
            INSERT INTO codec_context (
                operation_id, operation_type, message_type, schema_version,
                codec_type, tenant_id, user_id, correlation_id, payload_size,
                status, error_message, error_type, migration_used,
                source_version, target_version, validation_performed,
                validation_passed, context_state, metadata, created_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
                $14, $15, $16, $17, $18::jsonb, $19::jsonb, CURRENT_TIMESTAMP
            )
            RETURNING operation_id;
            """,
            params=(
                operation_id,
                operation_type,
                message_type,
                schema_version,
                codec_type,
                tenant_id,
                user_id,
                correlation_id,
                payload_size,
                status,
                error_message,
                error_type,
                migration_used,
                source_version,
                target_version,
                validation_performed,
                validation_passed,
                json.dumps(context_state) if context_state else None,
                json.dumps(metadata or {}),
            ),
            fetch_one=True,
        )
        return str(result["operation_id"]) if result else operation_id

    async def get_codec_history(
        self,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        message_type: Optional[str] = None,
        operation_type: Optional[str] = None,
        schema_version: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get codec operation history.

        Args:
            tenant_id: Tenant identifier for tenant isolation.
            user_id: Optional user identifier.
            message_type: Optional message type filter.
            operation_type: Optional operation type filter.
            schema_version: Optional schema version filter.
            status: Optional status filter.
            limit: Maximum number of records to return.
            offset: Offset for pagination.

        Returns:
            List of codec operation records.
        """
        query = """
        SELECT 
            operation_id, operation_type, message_type, schema_version,
            codec_type, tenant_id, user_id, correlation_id, payload_size,
            status, error_message, error_type, migration_used,
            source_version, target_version, validation_performed,
            validation_passed, context_state, metadata, created_at
        FROM codec_context
        WHERE 1=1
        """
        params: List[Any] = []
        param_count = 0

        if tenant_id:
            param_count += 1
            query += f" AND tenant_id = ${param_count}"
            params.append(tenant_id)
        if user_id:
            param_count += 1
            query += f" AND user_id = ${param_count}"
            params.append(user_id)
        if message_type:
            param_count += 1
            query += f" AND message_type = ${param_count}"
            params.append(message_type)
        if operation_type:
            param_count += 1
            query += f" AND operation_type = ${param_count}"
            params.append(operation_type)
        if schema_version:
            param_count += 1
            query += f" AND schema_version = ${param_count}"
            params.append(schema_version)
        if status:
            param_count += 1
            query += f" AND status = ${param_count}"
            params.append(status)

        query += f" ORDER BY created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
        params.extend([limit, offset])

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        if results:
            for record in results:
                if record.get("context_state"):
                    record["context_state"] = (
                        json.loads(record["context_state"])
                        if isinstance(record["context_state"], str)
                        else record["context_state"]
                    )
                if record.get("metadata"):
                    record["metadata"] = (
                        json.loads(record["metadata"])
                        if isinstance(record["metadata"], str)
                        else record["metadata"]
                    )
        return results if results else []

    async def get_schema_version_stats(
        self,
        message_type: Optional[str] = None,
        tenant_id: Optional[str] = None,
        time_range_hours: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get schema version usage statistics.

        Args:
            message_type: Optional message type filter.
            tenant_id: Tenant identifier for tenant isolation.
            time_range_hours: Optional time range in hours.

        Returns:
            Dictionary with schema version statistics.
        """
        query = """
        SELECT 
            schema_version,
            COUNT(*) as usage_count,
            COUNT(CASE WHEN operation_type = 'encode' THEN 1 END) as encode_count,
            COUNT(CASE WHEN operation_type = 'decode' THEN 1 END) as decode_count,
            COUNT(CASE WHEN status = 'success' THEN 1 END) as success_count,
            COUNT(CASE WHEN status = 'error' THEN 1 END) as error_count,
            COUNT(CASE WHEN migration_used = true THEN 1 END) as migration_count,
            AVG(payload_size) as avg_payload_size
        FROM codec_context
        WHERE 1=1
        """
        params: List[Any] = []
        param_count = 0

        if message_type:
            param_count += 1
            query += f" AND message_type = ${param_count}"
            params.append(message_type)
        if tenant_id:
            param_count += 1
            query += f" AND tenant_id = ${param_count}"
            params.append(tenant_id)
        if time_range_hours:
            param_count += 1
            query += f" AND created_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour' * ${param_count}"
            params.append(time_range_hours)

        query += """
        GROUP BY schema_version
        ORDER BY usage_count DESC
        """

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        if results:
            for record in results:
                record["avg_payload_size"] = float(record.get("avg_payload_size", 0) or 0)
                record["success_rate"] = (
                    (record["success_count"] / record["usage_count"]) * 100
                    if record["usage_count"] > 0
                    else 0.0
                )
            return list(results)  # Ensure it's a list
        return []

    async def get_serialization_context_state(
        self,
        correlation_id: str,
        tenant_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get serialization context state for a correlation ID.

        Args:
            correlation_id: Correlation identifier.
            tenant_id: Optional tenant identifier.

        Returns:
            List of codec operations with context state.
        """
        query = """
        SELECT 
            operation_id, operation_type, message_type, schema_version,
            codec_type, tenant_id, user_id, correlation_id, payload_size,
            status, error_message, error_type, migration_used,
            source_version, target_version, validation_performed,
            validation_passed, context_state, metadata, created_at
        FROM codec_context
        WHERE correlation_id = $1
        """
        params: List[Any] = [correlation_id]

        if tenant_id:
            query += " AND tenant_id = $2"
            params.append(tenant_id)

        query += " ORDER BY created_at ASC"

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        if results:
            for record in results:
                if record.get("context_state"):
                    record["context_state"] = (
                        json.loads(record["context_state"])
                        if isinstance(record["context_state"], str)
                        else record["context_state"]
                    )
                if record.get("metadata"):
                    record["metadata"] = (
                        json.loads(record["metadata"])
                        if isinstance(record["metadata"], str)
                        else record["metadata"]
                    )
        return results if results else []

    async def get_codec_operation_stats(
        self,
        tenant_id: Optional[str] = None,
        time_range_hours: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get codec operation statistics.

        Args:
            tenant_id: Tenant identifier for tenant isolation.
            time_range_hours: Optional time range in hours.

        Returns:
            Dictionary with codec operation statistics.
        """
        query = """
        SELECT 
            COUNT(*) as total_operations,
            COUNT(CASE WHEN operation_type = 'encode' THEN 1 END) as encode_operations,
            COUNT(CASE WHEN operation_type = 'decode' THEN 1 END) as decode_operations,
            COUNT(CASE WHEN status = 'success' THEN 1 END) as success_operations,
            COUNT(CASE WHEN status = 'error' THEN 1 END) as error_operations,
            COUNT(CASE WHEN migration_used = true THEN 1 END) as migration_operations,
            COUNT(CASE WHEN validation_performed = true THEN 1 END) as validation_operations,
            COUNT(CASE WHEN validation_passed = true THEN 1 END) as validation_passed_count,
            COUNT(CASE WHEN validation_passed = false THEN 1 END) as validation_failed_count,
            COUNT(DISTINCT message_type) as unique_message_types,
            COUNT(DISTINCT schema_version) as unique_schema_versions,
            AVG(payload_size) as avg_payload_size,
            MAX(payload_size) as max_payload_size,
            MIN(payload_size) as min_payload_size
        FROM codec_context
        WHERE 1=1
        """
        params: List[Any] = []
        param_count = 0

        if tenant_id:
            param_count += 1
            query += f" AND tenant_id = ${param_count}"
            params.append(tenant_id)
        if time_range_hours:
            param_count += 1
            query += f" AND created_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour' * ${param_count}"
            params.append(time_range_hours)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_one=True,
        )

        if result:
            total = result.get("total_operations", 0) or 0
            successes = result.get("success_operations", 0) or 0
            errors = result.get("error_operations", 0) or 0
            validations = result.get("validation_operations", 0) or 0
            validation_passed = result.get("validation_passed_count", 0) or 0

            return {
                "total_operations": total,
                "encode_operations": result.get("encode_operations", 0) or 0,
                "decode_operations": result.get("decode_operations", 0) or 0,
                "success_operations": successes,
                "error_operations": errors,
                "success_rate": (successes / total * 100) if total > 0 else 0.0,
                "error_rate": (errors / total * 100) if total > 0 else 0.0,
                "migration_operations": result.get("migration_operations", 0) or 0,
                "migration_rate": (result.get("migration_operations", 0) or 0) / total * 100 if total > 0 else 0.0,
                "validation_operations": validations,
                "validation_rate": (validations / total * 100) if total > 0 else 0.0,
                "validation_pass_rate": (validation_passed / validations * 100) if validations > 0 else 0.0,
                "unique_message_types": result.get("unique_message_types", 0) or 0,
                "unique_schema_versions": result.get("unique_schema_versions", 0) or 0,
                "avg_payload_size": float(result.get("avg_payload_size", 0) or 0),
                "max_payload_size": result.get("max_payload_size", 0) or 0,
                "min_payload_size": result.get("min_payload_size", 0) or 0,
            }
        return {
            "total_operations": 0,
            "encode_operations": 0,
            "decode_operations": 0,
            "success_operations": 0,
            "error_operations": 0,
            "success_rate": 0.0,
            "error_rate": 0.0,
            "migration_operations": 0,
            "migration_rate": 0.0,
            "validation_operations": 0,
            "validation_rate": 0.0,
            "validation_pass_rate": 0.0,
            "unique_message_types": 0,
            "unique_schema_versions": 0,
            "avg_payload_size": 0.0,
            "max_payload_size": 0,
            "min_payload_size": 0,
        }

    async def get_message_type_stats(
        self,
        tenant_id: Optional[str] = None,
        time_range_hours: Optional[int] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get message type usage statistics.

        Args:
            tenant_id: Tenant identifier for tenant isolation.
            time_range_hours: Optional time range in hours.
            limit: Maximum number of message types to return.

        Returns:
            List of message type statistics.
        """
        query = """
        SELECT 
            message_type,
            COUNT(*) as usage_count,
            COUNT(CASE WHEN operation_type = 'encode' THEN 1 END) as encode_count,
            COUNT(CASE WHEN operation_type = 'decode' THEN 1 END) as decode_count,
            COUNT(CASE WHEN status = 'success' THEN 1 END) as success_count,
            COUNT(CASE WHEN status = 'error' THEN 1 END) as error_count,
            COUNT(DISTINCT schema_version) as schema_versions_used,
            AVG(payload_size) as avg_payload_size
        FROM codec_context
        WHERE 1=1
        """
        params: List[Any] = []
        param_count = 0

        if tenant_id:
            param_count += 1
            query += f" AND tenant_id = ${param_count}"
            params.append(tenant_id)
        if time_range_hours:
            param_count += 1
            query += f" AND created_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour' * ${param_count}"
            params.append(time_range_hours)

        query += f"""
        GROUP BY message_type
        ORDER BY usage_count DESC
        LIMIT ${param_count + 1}
        """
        params.append(limit)

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        if results:
            for record in results:
                record["avg_payload_size"] = float(record.get("avg_payload_size", 0) or 0)
                record["success_rate"] = (
                    (record["success_count"] / record["usage_count"]) * 100
                    if record["usage_count"] > 0
                    else 0.0
                )
        return results if results else []

    async def cleanup_old_context(
        self,
        days: int = 90,
        tenant_id: Optional[str] = None,
    ) -> int:
        """
        Clean up old codec context records.

        Args:
            days: Number of days to keep (delete older records).
            tenant_id: Optional tenant identifier.

        Returns:
            Number of records deleted.
        """
        query = """
        DELETE FROM codec_context
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

