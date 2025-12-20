# Company Management API Reference

Complete API documentation for company creation and management endpoints.

---

## Table of Contents

1. [Create Company](#1-create-company)
2. [Get Companies (List)](#2-get-companies-list)
3. [Get Single Company](#3-get-single-company)
4. [Get Company Statistics](#4-get-company-statistics)
5. [Update Company](#5-update-company)
6. [Suspend Company](#6-suspend-company)
7. [Activate Company](#7-activate-company)
8. [Delete Company](#8-delete-company)
9. [Retry Failed Company](#9-retry-failed-company)

---

## 1. Create Company

Create a new company with a dedicated Frappe site.

### Endpoint
```
POST /api/method/pix_one.api.companies.create_companies.create_companies_service.create_company
```

### Authentication
Required - User must be logged in

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `company_name` | string | Yes | - | Company name (min 3 chars) |
| `company_abbr` | string | No | Auto-generated | Company abbreviation (max 10 chars) |
| `admin_password` | string | No | Auto-generated | Admin password for the site |
| `admin_email` | string | No | Current user | Admin email |
| `default_currency` | string | No | "USD" | Default currency code |
| `country` | string | No | "United States" | Country name |
| `domain` | string | No | null | Industry domain |
| `apps_to_install` | array/string | No | ["erpnext"] | Apps to install |
| `subscription_id` | string | No | Auto-detected | Subscription ID |

### Request Example

```javascript
frappe.call({
    method: "pix_one.api.companies.create_companies.create_companies_service.create_company",
    args: {
        company_name: "Acme Corporation",
        company_abbr: "ACME",
        default_currency: "USD",
        country: "United States",
        domain: "Manufacturing",
        apps_to_install: ["erpnext", "hrms"]
    },
    callback: function(r) {
        console.log(r.message);
    }
});
```

### Response (Success - 201 Created)

```json
{
    "success": true,
    "data": {
        "company_id": "COMP-2025-00001",
        "company_name": "Acme Corporation",
        "site_name": "acme-corporation",
        "site_url": "http://acme-corporation.localhost:8000",
        "admin_email": "user@example.com",
        "admin_password": "Xy9_kL2pQ8mN5vR",
        "status": "Active",
        "erpnext_company_id": "Acme Corporation",
        "provisioning_notes": "Site created: Site acme-corporation created successfully\nApps: Installed apps: erpnext, hrms\nERPNext company created: Acme Corporation"
    },
    "message": "Company 'Acme Corporation' created successfully with site 'acme-corporation'"
}
```

### Response (Error - 422 Validation Error)

```json
{
    "success": false,
    "message": "Company limit reached. Your 'Starter Plan' plan allows 1 company. You currently have 1. Please upgrade your subscription.",
    "error_code": "VALIDATION_ERROR",
    "details": {
        "quota": "EXCEEDED"
    },
    "http_status_code": 422
}
```

### Possible Errors

| HTTP Code | Error | Description |
|-----------|-------|-------------|
| 401 | Unauthorized | User not logged in |
| 422 | Validation Error | Invalid subscription or quota exceeded |
| 500 | Server Error | Site provisioning failed |

---

## 2. Get Companies (List)

Retrieve paginated list of companies for the current user.

### Endpoint
```
GET /api/method/pix_one.api.companies.get_companies.get_companies_service.get_companies
```

### Authentication
Required

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number (1-indexed) |
| `limit` | integer | No | 20 | Items per page |
| `search` | string | No | null | Search query (company name, site name) |
| `status` | string | No | null | Filter by status |
| `subscription_id` | string | No | null | Filter by subscription |
| `sort_by` | string | No | "creation" | Field to sort by |
| `sort_order` | string | No | "desc" | Sort order (asc/desc) |

### Request Example

```javascript
frappe.call({
    method: "pix_one.api.companies.get_companies.get_companies_service.get_companies",
    args: {
        page: 1,
        limit: 10,
        status: "Active",
        search: "acme",
        sort_by: "creation",
        sort_order: "desc"
    },
    callback: function(r) {
        console.log(r.message);
    }
});
```

### Response (Success - 200 OK)

```json
{
    "success": true,
    "data": [
        {
            "company_id": "COMP-2025-00001",
            "company_name": "Acme Corporation",
            "company_abbr": "ACME",
            "status": "Active",
            "site_name": "acme-corporation",
            "site_url": "http://acme-corporation.localhost:8000",
            "site_status": "Active",
            "subscription_id": "SUB-2025-00001",
            "erpnext_company_id": "Acme Corporation",
            "is_erpnext_synced": true,
            "created_at": "2025-12-20 10:30:00",
            "provisioning_completed_at": "2025-12-20 10:32:15"
        }
    ],
    "meta": {
        "total": 1,
        "page": 1,
        "limit": 10,
        "total_pages": 1
    },
    "message": "Found 1 companies"
}
```

---

## 3. Get Single Company

Get detailed information about a specific company.

### Endpoint
```
GET /api/method/pix_one.api.companies.get_companies.get_companies_service.get_company
```

### Authentication
Required

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `company_id` | string | Yes | Company ID (e.g., COMP-2025-00001) |

### Request Example

```javascript
frappe.call({
    method: "pix_one.api.companies.get_companies.get_companies_service.get_company",
    args: {
        company_id: "COMP-2025-00001"
    },
    callback: function(r) {
        console.log(r.message);
    }
});
```

### Response (Success - 200 OK)

```json
{
    "success": true,
    "data": {
        "company_id": "COMP-2025-00001",
        "company_name": "Acme Corporation",
        "company_abbr": "ACME",
        "status": "Active",
        "site_name": "acme-corporation",
        "site_url": "http://acme-corporation.localhost:8000",
        "site_status": "Active",
        "admin_email": "admin@acme.com",
        "default_currency": "USD",
        "country": "United States",
        "domain": "Manufacturing",
        "erpnext_company_id": "Acme Corporation",
        "is_erpnext_synced": true,
        "db_name": "_acme_corporation",
        "db_host": "mariadb",
        "db_port": "3306",
        "is_dedicated_db": false,
        "provisioning_started_at": "2025-12-20 10:30:00",
        "provisioning_completed_at": "2025-12-20 10:32:15",
        "last_accessed_at": "2025-12-20 15:45:30",
        "provisioning_notes": "...",
        "created_at": "2025-12-20 10:30:00",
        "created_by": "user@example.com",
        "subscription": {
            "subscription_id": "SUB-2025-00001",
            "subscription_status": "Active",
            "plan_name": "Professional Plan",
            "max_users": 25,
            "max_storage_mb": 25600,
            "max_companies": 3,
            "billing_interval": "Monthly",
            "next_billing_date": "2026-01-20"
        }
    },
    "message": "Company details retrieved successfully"
}
```

### Response (Error - 404 Not Found)

```json
{
    "success": false,
    "message": "Company COMP-2025-99999 not found",
    "error_code": "NOT_FOUND",
    "http_status_code": 404
}
```

---

## 4. Get Company Statistics

Get aggregated statistics for the current user's companies.

### Endpoint
```
GET /api/method/pix_one.api.companies.get_companies.get_companies_service.get_company_stats
```

### Authentication
Required

### Parameters
None

### Request Example

```javascript
frappe.call({
    method: "pix_one.api.companies.get_companies.get_companies_service.get_company_stats",
    callback: function(r) {
        console.log(r.message);
    }
});
```

### Response (Success - 200 OK)

```json
{
    "success": true,
    "data": {
        "total_companies": 3,
        "active_companies": 2,
        "provisioning_companies": 1,
        "failed_companies": 0,
        "suspended_companies": 0,
        "quota": {
            "max_companies": 3,
            "used_companies": 3,
            "available_companies": 0,
            "percentage_used": 100.0
        }
    },
    "message": "Statistics retrieved successfully"
}
```

---

## 5. Update Company

Update company details (not the site itself, just metadata).

### Endpoint
```
PUT /api/method/pix_one.api.companies.get_companies.get_companies_service.update_company
```

### Authentication
Required (must be owner or have write permission)

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `company_id` | string | Yes | Company ID |
| `company_name` | string | No | New company name |
| `admin_email` | string | No | New admin email |
| `default_currency` | string | No | New currency |
| `country` | string | No | New country |
| `domain` | string | No | New domain |

**Note:** Requires active subscription to update.

### Request Example

```javascript
frappe.call({
    method: "pix_one.api.companies.get_companies.get_companies_service.update_company",
    args: {
        company_id: "COMP-2025-00001",
        company_name: "Acme Corp (Updated)",
        admin_email: "newadmin@acme.com"
    },
    callback: function(r) {
        console.log(r.message);
    }
});
```

### Response (Success - 200 OK)

```json
{
    "success": true,
    "data": {
        "company_id": "COMP-2025-00001",
        "company_name": "Acme Corp (Updated)",
        "admin_email": "newadmin@acme.com",
        "default_currency": "USD",
        "country": "United States",
        "domain": "Manufacturing"
    },
    "message": "Company updated successfully"
}
```

---

## 6. Suspend Company

Suspend a company (makes it inaccessible but doesn't delete it).

### Endpoint
```
POST /api/method/pix_one.api.companies.get_companies.get_companies_service.suspend_company
```

### Authentication
Required (must be owner)

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `company_id` | string | Yes | Company ID |

### Request Example

```javascript
frappe.call({
    method: "pix_one.api.companies.get_companies.get_companies_service.suspend_company",
    args: {
        company_id: "COMP-2025-00001"
    },
    callback: function(r) {
        console.log(r.message);
    }
});
```

### Response (Success - 200 OK)

```json
{
    "success": true,
    "data": {
        "company_id": "COMP-2025-00001",
        "status": "Suspended"
    },
    "message": "Company 'Acme Corporation' has been suspended"
}
```

---

## 7. Activate Company

Activate a suspended company.

### Endpoint
```
POST /api/method/pix_one.api.companies.get_companies.get_companies_service.activate_company
```

### Authentication
Required (must be owner)

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `company_id` | string | Yes | Company ID |

### Request Example

```javascript
frappe.call({
    method: "pix_one.api.companies.get_companies.get_companies_service.activate_company",
    args: {
        company_id: "COMP-2025-00001"
    },
    callback: function(r) {
        console.log(r.message);
    }
});
```

### Response (Success - 200 OK)

```json
{
    "success": true,
    "data": {
        "company_id": "COMP-2025-00001",
        "status": "Active"
    },
    "message": "Company 'Acme Corporation' has been activated"
}
```

---

## 8. Delete Company

Delete a company and optionally drop its site.

### Endpoint
```
DELETE /api/method/pix_one.api.companies.create_companies.create_companies_service.delete_company
```

### Authentication
Required (must be owner or System Manager)

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `company_id` | string | Yes | - | Company ID |
| `drop_site` | boolean | No | false | Whether to drop the Frappe site |

**Warning:** Setting `drop_site=true` will permanently delete all data in the site database. This cannot be undone!

### Request Example

```javascript
frappe.call({
    method: "pix_one.api.companies.create_companies.create_companies_service.delete_company",
    args: {
        company_id: "COMP-2025-00001",
        drop_site: true
    },
    callback: function(r) {
        console.log(r.message);
    }
});
```

### Response (Success - 200 OK)

```json
{
    "success": true,
    "message": "Company Acme Corporation deleted successfully and site acme-corporation dropped"
}
```

---

## 9. Retry Failed Company

Retry provisioning for a failed company.

### Endpoint
```
POST /api/method/pix_one.api.companies.create_companies.create_companies_service.retry_failed_company
```

### Authentication
Required

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `company_id` | string | Yes | Failed company ID |

### Request Example

```javascript
frappe.call({
    method: "pix_one.api.companies.create_companies.create_companies_service.retry_failed_company",
    args: {
        company_id: "COMP-2025-00001"
    },
    callback: function(r) {
        console.log(r.message);
    }
});
```

### Response
Same as [Create Company](#1-create-company) response.

---

## Error Response Format

All endpoints return errors in a consistent format:

```json
{
    "success": false,
    "message": "Human-readable error message",
    "error_code": "ERROR_CODE",
    "details": {
        "field_name": "validation error details"
    },
    "http_status_code": 422
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | User not authenticated |
| `FORBIDDEN` | 403 | User lacks permission |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Invalid input or quota exceeded |
| `SERVER_ERROR` | 500 | Internal server error |

---

## Rate Limiting

Currently no rate limiting is implemented. For production, consider:

```python
# Example rate limiting (not implemented)
@frappe.whitelist()
@rate_limit(limit=10, window=60)  # 10 requests per minute
def create_company(...):
    pass
```

---

## Webhooks (Future Feature)

Future enhancement: Webhook notifications for company events.

### Potential Events
- `company.created` - Fired when company is created
- `company.provisioning.started` - Site provisioning started
- `company.provisioning.completed` - Site ready
- `company.provisioning.failed` - Provisioning failed
- `company.suspended` - Company suspended
- `company.activated` - Company activated
- `company.deleted` - Company deleted

---

## Testing

### cURL Examples

```bash
# Create company
curl -X POST https://your-domain.com/api/method/pix_one.api.companies.create_companies.create_companies_service.create_company \
  -H "Authorization: token YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Test Company",
    "default_currency": "USD"
  }'

# List companies
curl -X GET "https://your-domain.com/api/method/pix_one.api.companies.get_companies.get_companies_service.get_companies?page=1&limit=10" \
  -H "Authorization: token YOUR_API_TOKEN"

# Get company stats
curl -X GET https://your-domain.com/api/method/pix_one.api.companies.get_companies.get_companies_service.get_company_stats \
  -H "Authorization: token YOUR_API_TOKEN"
```

### Python Client Example

```python
import requests

BASE_URL = "https://your-domain.com"
API_TOKEN = "your_api_token"

headers = {
    "Authorization": f"token {API_TOKEN}",
    "Content-Type": "application/json"
}

# Create company
response = requests.post(
    f"{BASE_URL}/api/method/pix_one.api.companies.create_companies.create_companies_service.create_company",
    json={
        "company_name": "Python Test Company",
        "default_currency": "EUR"
    },
    headers=headers
)

print(response.json())

# List companies
response = requests.get(
    f"{BASE_URL}/api/method/pix_one.api.companies.get_companies.get_companies_service.get_companies",
    params={"page": 1, "limit": 10},
    headers=headers
)

print(response.json())
```

---

## API Versioning

Currently using unversioned endpoints. For future API versions:

```
/api/v1/companies/create
/api/v2/companies/create
```

---

## Support

For API issues or questions:
1. Check the [Implementation Guide](COMPANY_MANAGEMENT_GUIDE.md)
2. Review error messages and logs
3. Contact support at your-support@example.com

---

**Last Updated:** 2025-12-20
**API Version:** 1.0.0
