"""
Response Interceptor Module
Provides standardized API response formatting
"""

from typing import Any, Optional, Dict
import frappe
from functools import wraps


class ResponseFormatter:
    """Formats API responses in a standard structure"""

    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        meta: Optional[Dict] = None
    ) -> Dict:
        """
        Format a successful response

        Args:
            data: Response data
            message: Success message
            meta: Additional metadata (pagination info, etc.)

        Returns:
            Formatted response dictionary
        """
        response = {
            "success": True,
            "message": message,
            "data": data
        }

        if meta:
            response["meta"] = meta

        return response

    @staticmethod
    def error(
        message: str = "An error occurred",
        error_code: Optional[str] = None,
        details: Optional[Any] = None,
        http_status_code: int = 400
    ) -> Dict:
        """
        Format an error response

        Args:
            message: Error message
            error_code: Error code for client handling
            details: Additional error details
            http_status_code: HTTP status code

        Returns:
            Formatted error response dictionary
        """
        frappe.local.response['http_status_code'] = http_status_code

        response = {
            "success": False,
            "message": message
        }

        if error_code:
            response["error_code"] = error_code

        if details:
            response["details"] = details

        return response

    @staticmethod
    def paginated(
        data: list,
        total: int,
        page: int,
        limit: int,
        message: str = "Success"
    ) -> Dict:
        """
        Format a paginated response

        Args:
            data: List of items
            total: Total number of items
            page: Current page number
            limit: Items per page
            message: Success message

        Returns:
            Formatted paginated response
        """
        total_pages = (total + limit - 1) // limit  # Ceiling division

        meta = {
            "pagination": {
                "current_page": page,
                "per_page": limit,
                "total_items": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }

        return ResponseFormatter.success(data=data, message=message, meta=meta)

    @staticmethod
    def created(data: Any = None, message: str = "Resource created successfully") -> Dict:
        """
        Format a resource creation response

        Args:
            data: Created resource data
            message: Success message

        Returns:
            Formatted response with 201 status
        """
        frappe.local.response['http_status_code'] = 201
        return ResponseFormatter.success(data=data, message=message)

    @staticmethod
    def updated(data: Any = None, message: str = "Resource updated successfully") -> Dict:
        """
        Format a resource update response

        Args:
            data: Updated resource data
            message: Success message

        Returns:
            Formatted response
        """
        return ResponseFormatter.success(data=data, message=message)

    @staticmethod
    def deleted(message: str = "Resource deleted successfully") -> Dict:
        """
        Format a resource deletion response

        Args:
            message: Success message

        Returns:
            Formatted response with 204 status
        """
        frappe.local.response['http_status_code'] = 204
        return ResponseFormatter.success(message=message)

    @staticmethod
    def not_found(message: str = "Resource not found") -> Dict:
        """
        Format a not found response

        Args:
            message: Error message

        Returns:
            Formatted 404 response
        """
        return ResponseFormatter.error(
            message=message,
            error_code="NOT_FOUND",
            http_status_code=404
        )

    @staticmethod
    def unauthorized(message: str = "Unauthorized access") -> Dict:
        """
        Format an unauthorized response

        Args:
            message: Error message

        Returns:
            Formatted 401 response
        """
        return ResponseFormatter.error(
            message=message,
            error_code="UNAUTHORIZED",
            http_status_code=401
        )

    @staticmethod
    def forbidden(message: str = "Access forbidden") -> Dict:
        """
        Format a forbidden response

        Args:
            message: Error message

        Returns:
            Formatted 403 response
        """
        return ResponseFormatter.error(
            message=message,
            error_code="FORBIDDEN",
            http_status_code=403
        )

    @staticmethod
    def validation_error(message: str = "Validation failed", details: Optional[Any] = None) -> Dict:
        """
        Format a validation error response

        Args:
            message: Error message
            details: Validation error details

        Returns:
            Formatted 422 response
        """
        return ResponseFormatter.error(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            http_status_code=422
        )

    @staticmethod
    def server_error(message: str = "Internal server error") -> Dict:
        """
        Format a server error response

        Args:
            message: Error message

        Returns:
            Formatted 500 response
        """
        return ResponseFormatter.error(
            message=message,
            error_code="SERVER_ERROR",
            http_status_code=500
        )


def handle_exceptions(func):
    """
    Decorator to handle exceptions and return formatted error responses

    Usage:
        @frappe.whitelist()
        @handle_exceptions
        def my_api():
            # Your code here
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except frappe.PermissionError as e:
            frappe.log_error(frappe.get_traceback(), f"Permission Error in {func.__name__}")
            return ResponseFormatter.forbidden(str(e))
        except frappe.DoesNotExistError as e:
            return ResponseFormatter.not_found(str(e))
        except frappe.ValidationError as e:
            return ResponseFormatter.validation_error(str(e))
        except frappe.AuthenticationError as e:
            frappe.log_error(frappe.get_traceback(), f"Auth Error in {func.__name__}")
            return ResponseFormatter.unauthorized(str(e))
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), f"Error in {func.__name__}")
            return ResponseFormatter.server_error(str(e))
    return wrapper


def format_response(func):
    """
    Decorator to automatically format responses

    Usage:
        @frappe.whitelist()
        @format_response
        def my_api():
            return {"key": "value"}  # Will be wrapped in success response
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        # If result is already formatted (has 'success' key), return as-is
        if isinstance(result, dict) and 'success' in result:
            return result

        # Otherwise, wrap in success response
        return ResponseFormatter.success(data=result)
    return wrapper
