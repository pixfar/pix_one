"""
Base Pagination Module
Provides standardized pagination parameters for all API endpoints
"""

from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class PaginationParams:
    """Standard pagination parameters"""
    page: int = 1
    limit: int = 10
    sort: Optional[str] = None
    order: Optional[str] = None
    search: Optional[str] = None
    fields: str = '*'
    filters: Optional[Any] = None

    def __post_init__(self):
        """Validate pagination parameters"""
        # Convert string to int if needed
        if isinstance(self.page, str):
            self.page = int(self.page)
        if isinstance(self.limit, str):
            self.limit = int(self.limit)

        # Ensure positive values
        if self.page < 1:
            self.page = 1
        if self.limit < 1:
            self.limit = 10

        # Set max limit to prevent excessive queries
        if self.limit > 100:
            self.limit = 100

        # Normalize order
        if self.order and self.order.lower() not in ['asc', 'desc']:
            self.order = 'asc'

    @property
    def start(self) -> int:
        """Calculate the starting index for the query"""
        return (self.page - 1) * self.limit

    @property
    def order_by(self) -> Optional[str]:
        """Generate the order_by clause for frappe queries"""
        if self.sort:
            direction = self.order.upper() if self.order else 'ASC'
            return f"{self.sort} {direction}"
        return None

    def to_dict(self) -> dict:
        """Convert to dictionary for logging/debugging"""
        return {
            'page': self.page,
            'limit': self.limit,
            'sort': self.sort,
            'order': self.order,
            'search': self.search,
            'fields': self.fields,
            'filters': self.filters
        }


def get_pagination_params(page=1, limit=10, sort=None, order=None, search=None, fields='*', filters=None) -> PaginationParams:
    """
    Factory function to create PaginationParams from API parameters

    Args:
        page: Page number (default: 1)
        limit: Number of items per page (default: 10)
        sort: Field to sort by
        order: Sort order ('asc' or 'desc')
        search: Search term
        fields: Fields to return (default: '*')
        filters: Additional filters as dict or list

    Returns:
        PaginationParams instance
    """
    return PaginationParams(
        page=page,
        limit=limit,
        sort=sort,
        order=order,
        search=search,
        fields=fields,
        filters=filters
    )
