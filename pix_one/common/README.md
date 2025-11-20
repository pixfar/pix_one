# Common Services Documentation

This directory contains reusable services and utilities for building standardized APIs in the Pix One application.

## Overview

The common services provide:
- **Pagination**: Standardized pagination parameters
- **Data Service**: Reusable data fetching with pagination
- **Cache Service**: Redis caching operations
- **Response Interceptor**: Uniform API response formatting

## Directory Structure

```
common/
├── shared/
│   ├── base_pagination.py      # Pagination parameters and utilities
│   └── base_data_service.py    # Data fetching service
├── cache/
│   └── redis_cache_service.py  # Redis cache operations
├── interceptors/
│   └── response_interceptors.py # Response formatting
└── README.md
```

---

## 1. Base Pagination (`base_pagination.py`)

### Usage

```python
from pix_one.common.shared.base_pagination import get_pagination_params

# In your API function
pagination = get_pagination_params(
    page=1,
    limit=10,
    sort='creation',
    order='desc',
    search='test',
    fields='*',
    filters={'status': 'Active'}
)

# Access properties
print(pagination.start)      # 0 (calculated offset)
print(pagination.order_by)   # "creation DESC"
```

### Features

- **Auto-validation**: Ensures page >= 1, limit between 1-100
- **Type conversion**: Converts string inputs to integers
- **Calculated properties**: `start` offset and `order_by` clause
- **Flexible filters**: Supports dict or list format

### PaginationParams Properties

| Property | Type | Description |
|----------|------|-------------|
| `page` | int | Current page number (min: 1) |
| `limit` | int | Items per page (min: 1, max: 100) |
| `sort` | str | Field name to sort by |
| `order` | str | Sort direction ('asc' or 'desc') |
| `search` | str | Search term |
| `fields` | str | Fields to return |
| `filters` | dict/list | Query filters |
| `start` | int | Calculated offset for query |
| `order_by` | str | Formatted order clause |

---

## 2. Base Data Service (`base_data_service.py`)

### Usage

#### Get Paginated Data

```python
from pix_one.common.shared import BaseDataService, get_pagination_params

@frappe.whitelist()
def get_users(page=1, limit=10, search=None):
    pagination = get_pagination_params(page=page, limit=limit, search=search)

    # Get paginated data with count
    users, total = BaseDataService.get_paginated_data(
        doctype="User",
        pagination=pagination,
        search_fields=['email', 'full_name']  # Fields to search in
    )

    return {"users": users, "total": total}
```

#### Get List Without Pagination

```python
# Get all active plans
plans = BaseDataService.get_list_data(
    doctype="Subscription Plan",
    fields=['name', 'plan_name', 'price'],
    filters={'status': 'Active'},
    order_by='price ASC'
)
```

#### Get Single Document

```python
# Get specific document
user = BaseDataService.get_single_doc(
    doctype="User",
    name="user@example.com",
    fields=['email', 'full_name', 'role']
)

if user is None:
    # Handle not found
    pass
```

#### Count Records

```python
# Count matching records
active_count = BaseDataService.count_records(
    doctype="Subscription Plan",
    filters={'status': 'Active'}
)
```

#### Check Existence

```python
# Check if document exists
exists = BaseDataService.check_exists(
    doctype="User",
    name="user@example.com"
)
```

### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `get_paginated_data()` | doctype, pagination, additional_filters, search_fields | (list, int) | Get paginated results and total count |
| `get_list_data()` | doctype, fields, filters, order_by, limit | list | Get list without pagination |
| `get_single_doc()` | doctype, name, fields | dict or None | Get single document |
| `count_records()` | doctype, filters | int | Count matching records |
| `check_exists()` | doctype, name | bool | Check if document exists |

---

## 3. Redis Cache Service (`redis_cache_service.py`)

### Basic Operations

```python
from pix_one.common.cache import RedisCacheService

# Set value (expires in 5 minutes)
RedisCacheService.set('user:123', {'name': 'John'}, expires_in_sec=300)

# Get value
user = RedisCacheService.get('user:123')

# Delete value
RedisCacheService.delete('user:123')

# Delete by pattern
RedisCacheService.delete_pattern('user:*')

# Check existence
exists = RedisCacheService.exists('user:123')
```

### Counters

```python
# Increment counter
new_count = RedisCacheService.increment('page_views')
new_count = RedisCacheService.increment('page_views', delta=5)

# Decrement counter
new_count = RedisCacheService.decrement('credits')
```

### Hash Operations

```python
# Set hash field
RedisCacheService.set_hash('user:123', 'email', 'user@example.com')

# Get hash field
email = RedisCacheService.get_hash('user:123', 'email')

# Get all hash fields
user_data = RedisCacheService.get_all_hash('user:123')

# Delete hash field
RedisCacheService.delete_hash('user:123', 'email')
```

### Caching Decorator

```python
from pix_one.common.cache import cached

@cached(key_prefix='subscription_plans', expires_in_sec=600)
def get_all_plans():
    return frappe.get_all('Subscription Plan')

# First call: executes function and caches result
# Subsequent calls: returns cached result
plans = get_all_plans()
```

### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `get()` | key, default | Any | Get cached value |
| `set()` | key, value, expires_in_sec | bool | Set cache value |
| `delete()` | key | bool | Delete cache value |
| `delete_pattern()` | pattern | bool | Delete keys matching pattern |
| `exists()` | key | bool | Check if key exists |
| `increment()` | key, delta | int | Increment counter |
| `decrement()` | key, delta | int | Decrement counter |
| `set_hash()` | name, key, value | bool | Set hash field |
| `get_hash()` | name, key, default | Any | Get hash field |
| `get_all_hash()` | name | dict | Get all hash fields |
| `delete_hash()` | name, key | bool | Delete hash field |

---

## 4. Response Interceptor (`response_interceptors.py`)

### Standard Response Formats

#### Success Response

```python
from pix_one.common.interceptors import ResponseFormatter

@frappe.whitelist()
def get_data():
    data = {"key": "value"}
    return ResponseFormatter.success(
        data=data,
        message="Data retrieved successfully"
    )

# Response:
# {
#     "success": true,
#     "message": "Data retrieved successfully",
#     "data": {"key": "value"}
# }
```

#### Paginated Response

```python
@frappe.whitelist()
def get_items(page=1, limit=10):
    items = [...]
    total = 100

    return ResponseFormatter.paginated(
        data=items,
        total=total,
        page=page,
        limit=limit
    )

# Response:
# {
#     "success": true,
#     "message": "Success",
#     "data": [...],
#     "meta": {
#         "pagination": {
#             "current_page": 1,
#             "per_page": 10,
#             "total_items": 100,
#             "total_pages": 10,
#             "has_next": true,
#             "has_prev": false
#         }
#     }
# }
```

#### Error Response

```python
@frappe.whitelist()
def create_user(email):
    if not email:
        return ResponseFormatter.validation_error(
            message="Email is required",
            details={"field": "email", "error": "missing"}
        )

# Response (HTTP 422):
# {
#     "success": false,
#     "message": "Email is required",
#     "error_code": "VALIDATION_ERROR",
#     "details": {"field": "email", "error": "missing"}
# }
```

#### Other Response Types

```python
# 201 Created
return ResponseFormatter.created(
    data=new_user,
    message="User created successfully"
)

# 200 Updated
return ResponseFormatter.updated(
    data=updated_user,
    message="User updated successfully"
)

# 204 Deleted
return ResponseFormatter.deleted(
    message="User deleted successfully"
)

# 404 Not Found
return ResponseFormatter.not_found(
    message="User not found"
)

# 401 Unauthorized
return ResponseFormatter.unauthorized(
    message="Invalid credentials"
)

# 403 Forbidden
return ResponseFormatter.forbidden(
    message="You don't have permission to access this resource"
)

# 500 Server Error
return ResponseFormatter.server_error(
    message="An unexpected error occurred"
)
```

### Exception Handling Decorator

```python
from pix_one.common.interceptors import handle_exceptions

@frappe.whitelist()
@handle_exceptions
def my_api():
    # Automatically catches and formats:
    # - frappe.PermissionError -> 403 Forbidden
    # - frappe.DoesNotExistError -> 404 Not Found
    # - frappe.ValidationError -> 422 Validation Error
    # - frappe.AuthenticationError -> 401 Unauthorized
    # - Exception -> 500 Server Error

    user = frappe.get_doc("User", "nonexistent")  # Raises DoesNotExistError
    # Automatically returns formatted 404 response
```

### Auto-Format Decorator

```python
from pix_one.common.interceptors import format_response

@frappe.whitelist()
@format_response
def get_user():
    # Return plain data, it will be wrapped in success response
    return {"name": "John", "email": "john@example.com"}

# Response:
# {
#     "success": true,
#     "message": "Success",
#     "data": {"name": "John", "email": "john@example.com"}
# }
```

### Response Methods

| Method | Parameters | HTTP Status | Description |
|--------|------------|-------------|-------------|
| `success()` | data, message, meta | 200 | Success response |
| `paginated()` | data, total, page, limit, message | 200 | Paginated response |
| `created()` | data, message | 201 | Resource created |
| `updated()` | data, message | 200 | Resource updated |
| `deleted()` | message | 204 | Resource deleted |
| `error()` | message, error_code, details, http_status_code | Custom | Generic error |
| `not_found()` | message | 404 | Resource not found |
| `unauthorized()` | message | 401 | Unauthorized access |
| `forbidden()` | message | 403 | Access forbidden |
| `validation_error()` | message, details | 422 | Validation failed |
| `server_error()` | message | 500 | Server error |

---

## Complete Example: Building a Standard API

Here's a complete example combining all services:

```python
import frappe
from pix_one.common.shared import get_pagination_params, BaseDataService
from pix_one.common.cache import RedisCacheService, cached
from pix_one.common.interceptors import ResponseFormatter, handle_exceptions


@frappe.whitelist(allow_guest=True)
@handle_exceptions
def get_products(page=1, limit=10, sort=None, order=None, search=None, category=None):
    """
    Get products with pagination, caching, and standardized response
    """
    # 1. Get pagination parameters
    pagination = get_pagination_params(
        page=page,
        limit=limit,
        sort=sort,
        order=order,
        search=search,
        fields=['name', 'product_name', 'price', 'category', 'image']
    )

    # 2. Build cache key
    cache_key = f"products:{page}:{limit}:{sort}:{order}:{search}:{category}"

    # 3. Try to get from cache
    cached_response = RedisCacheService.get(cache_key)
    if cached_response:
        return cached_response

    # 4. Build additional filters
    additional_filters = {}
    if category:
        additional_filters['category'] = category

    # 5. Get paginated data
    products, total_count = BaseDataService.get_paginated_data(
        doctype="Product",
        pagination=pagination,
        additional_filters=additional_filters,
        search_fields=['product_name', 'description', 'sku']
    )

    # 6. Format response
    response = ResponseFormatter.paginated(
        data=products,
        total=total_count,
        page=pagination.page,
        limit=pagination.limit,
        message="Products retrieved successfully"
    )

    # 7. Cache the response for 5 minutes
    RedisCacheService.set(cache_key, response, expires_in_sec=300)

    return response


@frappe.whitelist()
@handle_exceptions
def create_product(product_name, price, category):
    """
    Create a new product
    """
    # Validate input
    if not product_name:
        return ResponseFormatter.validation_error(
            message="Product name is required",
            details={"field": "product_name"}
        )

    # Create document
    doc = frappe.get_doc({
        'doctype': 'Product',
        'product_name': product_name,
        'price': price,
        'category': category
    })
    doc.insert()

    # Invalidate cache
    RedisCacheService.delete_pattern('products:*')

    return ResponseFormatter.created(
        data=doc.as_dict(),
        message="Product created successfully"
    )


@frappe.whitelist()
@handle_exceptions
def get_product(name):
    """
    Get single product by name
    """
    # Try cache first
    cache_key = f"product:{name}"
    cached_product = RedisCacheService.get(cache_key)
    if cached_product:
        return ResponseFormatter.success(data=cached_product)

    # Get from database
    product = BaseDataService.get_single_doc("Product", name)

    if not product:
        return ResponseFormatter.not_found(
            message=f"Product '{name}' not found"
        )

    # Cache for 10 minutes
    RedisCacheService.set(cache_key, product, expires_in_sec=600)

    return ResponseFormatter.success(
        data=product,
        message="Product retrieved successfully"
    )


@frappe.whitelist()
@handle_exceptions
def delete_product(name):
    """
    Delete a product
    """
    # Check if exists
    if not BaseDataService.check_exists("Product", name):
        return ResponseFormatter.not_found(
            message=f"Product '{name}' not found"
        )

    # Delete document
    frappe.delete_doc("Product", name)

    # Invalidate cache
    RedisCacheService.delete(f"product:{name}")
    RedisCacheService.delete_pattern('products:*')

    return ResponseFormatter.deleted(
        message="Product deleted successfully"
    )
```

---

## Best Practices

### 1. Always Use Pagination for List APIs
```python
# ✅ Good
pagination = get_pagination_params(page=page, limit=limit)
data, total = BaseDataService.get_paginated_data(...)

# ❌ Bad
data = frappe.get_all("DocType")  # No pagination
```

### 2. Cache Expensive Queries
```python
# ✅ Good - Cache results
cache_key = f"expensive_query:{param}"
result = RedisCacheService.get(cache_key)
if not result:
    result = perform_expensive_query()
    RedisCacheService.set(cache_key, result, expires_in_sec=300)

# ❌ Bad - No caching
result = perform_expensive_query()  # Runs every time
```

### 3. Use Exception Handling Decorator
```python
# ✅ Good
@frappe.whitelist()
@handle_exceptions
def my_api():
    # Exceptions are automatically caught and formatted
    pass

# ❌ Bad
@frappe.whitelist()
def my_api():
    try:
        # Manual exception handling
    except Exception as e:
        return {"error": str(e)}  # Non-standard format
```

### 4. Invalidate Cache on Updates
```python
# ✅ Good
def update_product(name, data):
    frappe.db.set_value("Product", name, data)
    RedisCacheService.delete(f"product:{name}")
    RedisCacheService.delete_pattern('products:*')

# ❌ Bad
def update_product(name, data):
    frappe.db.set_value("Product", name, data)
    # Cache not invalidated - stale data!
```

### 5. Use Consistent Response Format
```python
# ✅ Good
return ResponseFormatter.success(data=result)
return ResponseFormatter.paginated(data=items, total=count, ...)

# ❌ Bad
return {"data": result}  # Inconsistent format
return items  # No metadata
```

---

## Migration Guide

### Before (Old API)
```python
@frappe.whitelist()
def get_plans(page=1, limit=10):
    plans = frappe.get_all("Subscription Plan")
    return plans
```

### After (Using Common Services)
```python
@frappe.whitelist()
@handle_exceptions
def get_plans(page=1, limit=10, sort=None, order=None, search=None):
    pagination = get_pagination_params(
        page=page, limit=limit, sort=sort, order=order, search=search
    )

    cache_key = f"plans:{pagination.page}:{pagination.limit}"
    cached_data = RedisCacheService.get(cache_key)
    if cached_data:
        return cached_data

    plans, total = BaseDataService.get_paginated_data(
        doctype="Subscription Plan",
        pagination=pagination,
        search_fields=['plan_name', 'description']
    )

    response = ResponseFormatter.paginated(
        data=plans,
        total=total,
        page=pagination.page,
        limit=pagination.limit
    )

    RedisCacheService.set(cache_key, response, expires_in_sec=300)
    return response
```

### Benefits
- ✅ Standardized pagination
- ✅ Automatic caching
- ✅ Consistent response format
- ✅ Error handling
- ✅ Search support
- ✅ Sorting support
- ✅ Performance optimized

---

## Troubleshooting

### Cache Not Working
- Ensure Redis is running: `bench redis-cache`
- Check cache configuration in `site_config.json`
- Verify cache key uniqueness

### Import Errors
- Ensure `__init__.py` files exist in all directories
- Use correct import paths: `from pix_one.common.shared import ...`
- Restart Frappe: `bench restart`

### Pagination Issues
- Verify page and limit are positive integers
- Check if sort field exists in DocType
- Ensure order is 'asc' or 'desc'

---

## Support

For issues or questions, contact the development team or create an issue in the project repository.
