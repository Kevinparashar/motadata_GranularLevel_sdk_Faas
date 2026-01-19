"""
Access Control Framework

Manages permissions for agents and tools created through prompt-based generation.
"""

from typing import Dict, List, Optional, Set
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime

from .exceptions import AccessControlError


class Permission(str, Enum):
    """Permission types."""
    READ = "read"           # View agent/tool
    EXECUTE = "execute"     # Use agent/tool
    CREATE = "create"       # Create new agents/tools
    DELETE = "delete"       # Delete agents/tools
    ADMIN = "admin"         # Full access


class ResourceType(str, Enum):
    """Resource types."""
    AGENT = "agent"
    TOOL = "tool"


class PermissionEntry(BaseModel):
    """Permission entry for a resource."""
    resource_type: ResourceType
    resource_id: str
    permissions: List[Permission] = Field(default_factory=list)
    granted_at: datetime = Field(default_factory=datetime.now)
    granted_by: Optional[str] = None


class AccessControl:
    """
    Access control framework for managing permissions.
    
    Provides fine-grained access control for agents and tools
    with tenant isolation and user-level permissions.
    """
    
    def __init__(self):
        """Initialize access control."""
        # Structure: {tenant_id: {user_id: {resource_type: {resource_id: [permissions]}}}}
        self._permissions: Dict[str, Dict[str, Dict[str, Dict[str, List[Permission]]]]] = {}
        
        # Default permissions per tenant
        self._default_permissions: Dict[str, List[Permission]] = {}
    
    def grant_permission(
        self,
        tenant_id: str,
        user_id: str,
        resource_type: ResourceType,
        resource_id: str,
        permission: Permission,
        granted_by: Optional[str] = None
    ) -> None:
        """
        Grant permission to a user for a resource.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            resource_type: Type of resource (agent/tool)
            resource_id: Resource ID
            permission: Permission to grant
            granted_by: ID of user granting permission
        """
        if tenant_id not in self._permissions:
            self._permissions[tenant_id] = {}
        
        if user_id not in self._permissions[tenant_id]:
            self._permissions[tenant_id][user_id] = {}
        
        if resource_type.value not in self._permissions[tenant_id][user_id]:
            self._permissions[tenant_id][user_id][resource_type.value] = {}
        
        if resource_id not in self._permissions[tenant_id][user_id][resource_type.value]:
            self._permissions[tenant_id][user_id][resource_type.value][resource_id] = []
        
        if permission not in self._permissions[tenant_id][user_id][resource_type.value][resource_id]:
            self._permissions[tenant_id][user_id][resource_type.value][resource_id].append(permission)
    
    def revoke_permission(
        self,
        tenant_id: str,
        user_id: str,
        resource_type: ResourceType,
        resource_id: str,
        permission: Permission
    ) -> None:
        """
        Revoke permission from a user for a resource.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            resource_type: Type of resource (agent/tool)
            resource_id: Resource ID
            permission: Permission to revoke
        """
        if tenant_id not in self._permissions:
            return
        
        if user_id not in self._permissions[tenant_id]:
            return
        
        if resource_type.value not in self._permissions[tenant_id][user_id]:
            return
        
        if resource_id not in self._permissions[tenant_id][user_id][resource_type.value]:
            return
        
        if permission in self._permissions[tenant_id][user_id][resource_type.value][resource_id]:
            self._permissions[tenant_id][user_id][resource_type.value][resource_id].remove(permission)
    
    def check_permission(
        self,
        tenant_id: str,
        user_id: str,
        resource_type: ResourceType,
        resource_id: str,
        permission: Permission
    ) -> bool:
        """
        Check if user has permission for a resource.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            resource_type: Type of resource (agent/tool)
            resource_id: Resource ID
            permission: Permission to check
            
        Returns:
            True if user has permission, False otherwise
        """
        # Check tenant isolation first
        if tenant_id not in self._permissions:
            return False
        
        if user_id not in self._permissions[tenant_id]:
            return False
        
        if resource_type.value not in self._permissions[tenant_id][user_id]:
            return False
        
        if resource_id not in self._permissions[tenant_id][user_id][resource_type.value]:
            return False
        
        user_permissions = self._permissions[tenant_id][user_id][resource_type.value][resource_id]
        
        # ADMIN permission grants all permissions
        if Permission.ADMIN in user_permissions:
            return True
        
        # Check specific permission
        return permission in user_permissions
    
    def require_permission(
        self,
        tenant_id: str,
        user_id: str,
        resource_type: ResourceType,
        resource_id: str,
        permission: Permission
    ) -> None:
        """
        Require permission, raise exception if not granted.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            resource_type: Type of resource (agent/tool)
            resource_id: Resource ID
            permission: Required permission
            
        Raises:
            AccessControlError: If permission is not granted
        """
        if not self.check_permission(tenant_id, user_id, resource_type, resource_id, permission):
            raise AccessControlError(
                message=f"Permission denied: {user_id} does not have {permission.value} permission for {resource_type.value} {resource_id}",
                tenant_id=tenant_id,
                user_id=user_id,
                resource_type=resource_type.value,
                resource_id=resource_id,
                permission=permission.value
            )
    
    def get_user_permissions(
        self,
        tenant_id: str,
        user_id: str,
        resource_type: Optional[ResourceType] = None
    ) -> Dict[str, List[Permission]]:
        """
        Get all permissions for a user.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            resource_type: Optional resource type filter
            
        Returns:
            Dictionary mapping resource_id to list of permissions
        """
        if tenant_id not in self._permissions:
            return {}
        
        if user_id not in self._permissions[tenant_id]:
            return {}
        
        user_perms = self._permissions[tenant_id][user_id]
        
        if resource_type:
            if resource_type.value not in user_perms:
                return {}
            return user_perms[resource_type.value].copy()
        
        # Return all permissions
        all_perms = {}
        for rt, resources in user_perms.items():
            all_perms.update(resources)
        
        return all_perms
    
    def set_default_permissions(
        self,
        tenant_id: str,
        permissions: List[Permission]
    ) -> None:
        """
        Set default permissions for a tenant.
        
        Args:
            tenant_id: Tenant ID
            permissions: List of default permissions
        """
        self._default_permissions[tenant_id] = permissions
    
    def get_default_permissions(self, tenant_id: str) -> List[Permission]:
        """
        Get default permissions for a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            List of default permissions
        """
        return self._default_permissions.get(tenant_id, [Permission.READ, Permission.EXECUTE])

