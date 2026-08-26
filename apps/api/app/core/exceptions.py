"""
Custom exception classes for RazorGrowth AI.

These map to the standard error codes defined in the API specification.
"""


class RazorGrowthError(Exception):
    """Base exception for all RazorGrowth errors."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
        details: dict | None = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class AuthenticationError(RazorGrowthError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication required."):
        super().__init__(
            code="AUTHENTICATION_REQUIRED",
            message=message,
            status_code=401,
        )


class InvalidTokenError(RazorGrowthError):
    """Raised when the provided token is invalid or expired."""

    def __init__(self, message: str = "Invalid or expired token."):
        super().__init__(
            code="INVALID_TOKEN",
            message=message,
            status_code=401,
        )


class ForbiddenError(RazorGrowthError):
    """Raised when the user lacks permission for the action."""

    def __init__(self, message: str = "You do not have permission to perform this action."):
        super().__init__(
            code="FORBIDDEN",
            message=message,
            status_code=403,
        )


class TenantAccessDeniedError(RazorGrowthError):
    """Raised when cross-tenant access is attempted."""

    def __init__(self, message: str = "Access to this tenant is denied."):
        super().__init__(
            code="TENANT_ACCESS_DENIED",
            message=message,
            status_code=403,
        )


class NotFoundError(RazorGrowthError):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str = "Resource", message: str | None = None):
        super().__init__(
            code="RESOURCE_NOT_FOUND",
            message=message or f"{resource} not found.",
            status_code=404,
        )


class ConflictError(RazorGrowthError):
    """Raised when a resource conflict occurs (e.g., duplicate)."""

    def __init__(self, message: str = "Resource already exists."):
        super().__init__(
            code="CONFLICT",
            message=message,
            status_code=409,
        )


class ValidationError(RazorGrowthError):
    """Raised when input validation fails beyond Pydantic."""

    def __init__(self, message: str = "Validation error.", details: dict | None = None):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=422,
            details=details,
        )
