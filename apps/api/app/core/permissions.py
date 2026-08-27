from enum import Enum

class PermissionEnum(str, Enum):
    # Catalog
    CATALOG_READ = "catalog.read"
    CATALOG_WRITE = "catalog.write"
    
    # API Keys
    API_KEYS_READ = "api_keys.read"
    API_KEYS_WRITE = "api_keys.write"
    
    # Tenants
    TENANT_READ = "tenant.read"
    TENANT_WRITE = "tenant.write"
