"""
Base Data Service Module
Provides standardized data retrieval with pagination support
"""

import frappe
from typing import Optional, List, Dict, Any, Tuple
from pix_one.common.shared.base_pagination import PaginationParams


class BaseDataService:
    """Service for handling common data operations with pagination"""
    @staticmethod
    def get_current_user():
        """Get the current user document"""
        user = frappe.session.user
        userInfo = BaseDataService.get_list_data(
            doctype="User",
            filters={"name": user},
            fields="name, email, first_name, last_name, full_name")
        for user in userInfo:
            user['contacts'] = BaseDataService.get_list_data(
                doctype="Contact",
                fields="*",
                filters={"email_id": user['name']},
                order_by="modified desc"
            )
            user['roles'] = frappe.get_roles(user['name'])
        return userInfo

    @staticmethod
    def get_paginated_data(
        doctype: str,
        pagination: PaginationParams,
        additional_filters: Optional[Dict] = None,
        search_fields: Optional[List[str]] = None
    ) -> Tuple[List[Dict], int]:
        """
        Get paginated data from a DocType with total count

        Args:
            doctype: DocType name to query
            pagination: PaginationParams instance
            additional_filters: Additional filters to apply
            search_fields: List of fields to search in when search term is provided

        Returns:
            Tuple of (data list, total count)
        """
        # Build filters
        filters = BaseDataService._build_filters(
            pagination.filters,
            additional_filters,
            pagination.search,
            search_fields
        )

        # Get total count
        total_count = frappe.db.count(doctype, filters=filters)

        # Get paginated data
        data = frappe.get_all(
            doctype,
            fields=pagination.fields,
            filters=filters,
            start=pagination.start,
            page_length=pagination.limit,
            order_by=pagination.order_by
        )

        return data, total_count

    @staticmethod
    def get_list_data(
        doctype: str,
        fields: str = '*',
        filters: Optional[Any] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get list data without pagination

        Args:
            doctype: DocType name
            fields: Fields to return
            filters: Query filters
            order_by: Order by clause
            limit: Maximum number of records

        Returns:
            List of records
        """
        return frappe.get_all(
            doctype,
            fields=fields,
            filters=filters,
            order_by=order_by,
            limit_page_length=limit
        )

    @staticmethod
    def get_single_doc(doctype: str, name: str, fields: str = '*') -> Optional[Dict]:
        """
        Get a single document

        Args:
            doctype: DocType name
            name: Document name
            fields: Fields to return

        Returns:
            Document data or None if not found
        """
        try:
            return frappe.get_doc(doctype, name).as_dict()
        except frappe.DoesNotExistError:
            return None

    @staticmethod
    def _build_filters(
        base_filters: Optional[Any],
        additional_filters: Optional[Dict],
        search_term: Optional[str],
        search_fields: Optional[List[str]]
    ) -> Any:
        """
        Build combined filters including search

        Args:
            base_filters: Base filters from pagination
            additional_filters: Additional filters to merge
            search_term: Search term to apply
            search_fields: Fields to search in

        Returns:
            Combined filters
        """
        filters = {}

        # Handle base filters
        if base_filters:
            if isinstance(base_filters, dict):
                filters.update(base_filters)
            else:
                return base_filters  # Return as-is if it's a list or other format

        # Add additional filters
        if additional_filters:
            filters.update(additional_filters)

        # Handle search
        if search_term and search_fields:
            # Create OR conditions for search across multiple fields
            search_conditions = []
            for field in search_fields:
                search_conditions.append([field, 'like', f'%{search_term}%'])

            if search_conditions:
                if filters:
                    # Combine existing filters with search conditions
                    return ['and', filters, ['or'] + search_conditions]
                else:
                    return ['or'] + search_conditions

        return filters if filters else None

    @staticmethod
    def count_records(doctype: str, filters: Optional[Any] = None) -> int:
        """
        Count records matching filters

        Args:
            doctype: DocType name
            filters: Query filters

        Returns:
            Number of records
        """
        return frappe.db.count(doctype, filters=filters)

    @staticmethod
    def check_exists(doctype: str, name: str) -> bool:
        """
        Check if a document exists

        Args:
            doctype: DocType name
            name: Document name

        Returns:
            True if exists, False otherwise
        """
        return frappe.db.exists(doctype, name)
