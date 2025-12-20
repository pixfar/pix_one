# SaaS Company Management Implementation Guide

## Overview

This guide explains the complete implementation of the company creation workflow for your SaaS ERP solution. The system creates **one site per company** within a single bench infrastructure, NOT separate benches per company.

## Architecture Decision: Sites vs. Benches

### Why Sites, Not Benches?

**Chosen Approach: 1 Bench → Multiple Sites (1 site per company)**

#### Advantages:
- ✅ **Standard Frappe multi-tenancy pattern** - Battle-tested and recommended by Frappe
- ✅ **Resource efficient** - Sites share the same codebase, significantly reducing disk and memory usage
- ✅ **Easy maintenance** - Update apps once, all sites benefit
- ✅ **Fast provisioning** - Creating a site takes seconds vs. minutes for a bench
- ✅ **Scalable** - Handle thousands of companies on a single bench
- ✅ **Cost-effective** - Minimal infrastructure overhead

#### Alternative (Not Recommended): 1 Bench per Company
- ❌ **Massive resource overhead** - Each bench duplicates entire codebase (~500MB+ per bench)
- ❌ **Complex orchestration** - Requires container orchestration (Kubernetes, Docker Swarm)
- ❌ **Maintenance nightmare** - Updating 100 companies means 100 separate bench updates
- ❌ **Slow provisioning** - Bench creation takes 5-10 minutes minimum
- ❌ **Infrastructure costs** - Each bench needs dedicated resources

---

## Implementation Components

### 1. DocType: `SaaS Company`

**Location:** [pix_one/pix_one/doctype/saas_company/](pix_one/pix_one/doctype/saas_company/)

**Key Fields:**
- `company_name` - Company name
- `company_abbr` - Company abbreviation
- `site_name` - Unique site identifier (auto-generated)
- `site_url` - Full site URL
- `status` - Draft | Provisioning | Active | Suspended | Deleted | Failed
- `subscription_id` - Link to SaaS Subscriptions
- `customer_id` - Link to User (owner)
- `erpnext_company_id` - ERPNext Company ID on the provisioned site
- `admin_password` - Site admin password
- `db_name`, `db_host`, `db_port` - Database details

**Automatic Features:**
- Site name generation from company name (sanitized, unique)
- Subscription validation and quota enforcement
- Automatic company count tracking
- ERPNext integration support

---

### 2. API Services

#### 2.1 Company Creation Service

**Location:** [pix_one/api/companies/create-companies/create-companies.service.py](pix_one/api/companies/create-companies/create-companies.service.py)

**Main Endpoint:**
```python
@frappe.whitelist()
def create_company(
    company_name: str,
    company_abbr: Optional[str] = None,
    admin_password: Optional[str] = None,
    admin_email: Optional[str] = None,
    default_currency: str = "USD",
    country: str = "United States",
    domain: Optional[str] = None,
    apps_to_install: Optional[list] = None,
    subscription_id: Optional[str] = None
) -> Dict[str, Any]
```

**Features:**
- ✅ **Subscription Validation** - Ensures user has active subscription
- ✅ **Quota Enforcement** - Checks company limit from subscription plan
- ✅ **Auto-password Generation** - Generates secure password if not provided
- ✅ **Site Provisioning** - Creates Frappe site via bench CLI
- ✅ **App Installation** - Installs specified apps (default: ERPNext)
- ✅ **ERPNext Company Creation** - Auto-creates Company doctype in ERPNext
- ✅ **Error Handling** - Comprehensive error handling with rollback
- ✅ **Lock Management** - Handles stale lock files

**Workflow:**
1. Validate user authentication
2. Validate active subscription exists
3. Check company quota (max_companies from plan)
4. Create SaaS Company document (status: Draft)
5. Generate unique site name
6. Provision Frappe site using `bench new-site`
7. Install specified apps (e.g., erpnext)
8. Create ERPNext Company record
9. Update status to Active
10. Return site credentials

**Other Endpoints:**
- `retry_failed_company(company_id)` - Retry failed provisioning
- `delete_company(company_id, drop_site)` - Delete company and optionally drop site

#### 2.2 Company Retrieval Service

**Location:** [pix_one/api/companies/get-companies/get-companies.service.py](pix_one/api/companies/get-companies/get-companies.service.py)

**Endpoints:**

```python
# List companies with pagination
@frappe.whitelist()
def get_companies(page=1, limit=20, search=None, status=None,
                  subscription_id=None, sort_by="creation", sort_order="desc")

# Get single company details
@frappe.whitelist()
def get_company(company_id: str)

# Get company statistics
@frappe.whitelist()
def get_company_stats()

# Update company details
@frappe.whitelist()
def update_company(company_id: str, company_name=None, admin_email=None, ...)

# Suspend/Activate company
@frappe.whitelist()
def suspend_company(company_id: str)

@frappe.whitelist()
def activate_company(company_id: str)
```

---

### 3. Subscription Hooks

**Location:** [pix_one/utils/company_hooks.py](pix_one/utils/company_hooks.py)

**Functions:**

1. **`update_subscription_on_company_change`** (after_insert, on_trash)
   - Automatically updates `current_companies` count in SaaS Subscriptions
   - Syncs count to SaaS App Validation (license)

2. **`validate_company_on_subscription_change`** (on_update)
   - Suspends all companies when subscription becomes inactive
   - Handles plan downgrades by suspending excess companies

3. **`auto_activate_companies_on_subscription_renewal`** (on_update)
   - Reactivates companies when subscription renews from Past Due/Expired

**Hook Registration:** [pix_one/hooks.py](pix_one/hooks.py)

```python
doc_events = {
    "SaaS Company": {
        "after_insert": "pix_one.utils.company_hooks.update_subscription_on_company_change",
        "on_trash": "pix_one.utils.company_hooks.update_subscription_on_company_change"
    },
    "SaaS Subscriptions": {
        "on_update": [
            "pix_one.utils.company_hooks.validate_company_on_subscription_change",
            "pix_one.utils.company_hooks.auto_activate_companies_on_subscription_renewal"
        ]
    }
}
```

---

## API Usage Examples

### Example 1: Create a Company

```javascript
// Frontend API call
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
        if (r.message.success) {
            console.log("Company created:", r.message.data);
            // Response includes:
            // - company_id
            // - site_name (e.g., "acme-corporation")
            // - site_url (e.g., "http://acme-corporation.localhost:8000")
            // - admin_password (only on creation)
            // - erpnext_company_id
        }
    }
});
```

### Example 2: List User's Companies

```javascript
frappe.call({
    method: "pix_one.api.companies.get_companies.get_companies_service.get_companies",
    args: {
        page: 1,
        limit: 10,
        status: "Active"
    },
    callback: function(r) {
        if (r.message.success) {
            console.log("Companies:", r.message.data);
            console.log("Total:", r.message.meta.total);
        }
    }
});
```

### Example 3: Get Company Statistics

```javascript
frappe.call({
    method: "pix_one.api.companies.get_companies.get_companies_service.get_company_stats",
    callback: function(r) {
        if (r.message.success) {
            const stats = r.message.data;
            console.log(`Active: ${stats.active_companies}`);
            console.log(`Quota: ${stats.quota.used_companies}/${stats.quota.max_companies}`);
            console.log(`Available: ${stats.quota.available_companies}`);
        }
    }
});
```

---

## Subscription Plan Configuration

### Required Fields in `SaaS Subscription Plan`

Ensure your subscription plans have:

```json
{
    "plan_name": "Starter Plan",
    "max_companies": 1,        // KEY: Maximum companies allowed
    "max_users": 5,
    "max_storage_mb": 5120,
    "billing_interval": "Monthly",
    "price": 49.99
}
```

**Plan Tiers Example:**

| Plan | max_companies | max_users | max_storage_mb | price |
|------|---------------|-----------|----------------|-------|
| Starter | 1 | 5 | 5 GB | $49 |
| Professional | 3 | 25 | 25 GB | $199 |
| Enterprise | 10 | 100 | 100 GB | $999 |
| Unlimited | 999 | 999 | 500 GB | $2999 |

---

## Environment Configuration

### Required Environment Variables

```bash
# Database Configuration
export DB_HOST="mariadb"
export DB_PORT="3306"
export DB_ROOT_USER="root"
export DB_ROOT_PASSWORD="your_secure_password"

# Bench Path
export BENCH_PATH="/workspace/development/saas-bench"
```

### Site Config (`sites/common_site_config.json`)

```json
{
    "db_host": "mariadb",
    "db_port": 3306,
    "db_root_username": "root",
    "db_root_password": "your_secure_password",
    "redis_cache": "redis://redis:6379",
    "redis_queue": "redis://redis:6379",
    "redis_socketio": "redis://redis:6379"
}
```

---

## Installation & Setup

### Step 1: Install the DocType

```bash
cd /workspace/development/saas-bench
bench --site saas.localhost migrate
```

This will create the `SaaS Company` doctype.

### Step 2: Verify Installation

```bash
# Check if doctype exists
bench --site saas.localhost console

>>> import frappe
>>> frappe.get_meta("SaaS Company")
```

### Step 3: Grant Permissions

Create a role called "Subscriber" and assign permissions:

```bash
bench --site saas.localhost console

>>> import frappe
>>> # Subscribers can create/read/update their own companies
>>> frappe.get_doc({
...     "doctype": "Custom Role Permission",
...     "role": "Subscriber",
...     "document_type": "SaaS Company",
...     "select": 1,
...     "read": 1,
...     "write": 1,
...     "create": 1,
...     "if_owner": 1
... }).insert()
```

### Step 4: Test Company Creation

```python
# In bench console
import frappe
from pix_one.api.companies.create_companies.create_companies_service import create_company

frappe.set_user("test@example.com")  # User with active subscription

result = create_company(
    company_name="Test Company",
    apps_to_install=["erpnext"]
)

print(result)
```

---

## Workflow Diagrams

### Company Creation Flow

```
User Request
    ↓
[Validate Authentication]
    ↓
[Validate Active Subscription] ← Checks SaaS Subscriptions (status=Active)
    ↓
[Check Company Quota] ← Reads max_companies from Plan
    ↓
[Create SaaS Company Doc] → status: Draft
    ↓
[Generate Site Name] → e.g., "acme-corp-1"
    ↓
[Run: bench new-site acme-corp-1]
    ↓
[Install Apps] → bench --site acme-corp-1 install-app erpnext
    ↓
[Create ERPNext Company] → via bench console
    ↓
[Update Status] → Active
    ↓
[Update Subscription Count] → current_companies++
    ↓
[Return Response] → site_name, site_url, credentials
```

### Subscription Downgrade Flow

```
User Downgrades Plan (3 companies → 1 company)
    ↓
[SaaS Subscriptions on_update hook triggered]
    ↓
[validate_company_on_subscription_change]
    ↓
[Count active companies] → finds 3 companies
    ↓
[New plan allows max 1 company]
    ↓
[Keep oldest 1 company Active]
    ↓
[Suspend excess 2 companies] → status: Suspended
    ↓
[Show warning to user] → "Suspended 2 companies due to plan downgrade"
```

---

## Error Handling

### Common Errors and Solutions

#### 1. "No active subscription found"
**Cause:** User doesn't have an active subscription
**Solution:** User must purchase a subscription plan first

#### 2. "Company limit reached"
**Cause:** User has reached max_companies quota
**Solution:** Upgrade subscription plan or delete existing companies

#### 3. "Site provisioning failed: DB root password not provided"
**Cause:** DB_ROOT_PASSWORD not set
**Solution:** Set environment variable or update site_config.json

#### 4. "bench_new_site.lock present"
**Cause:** Previous site creation failed mid-process
**Solution:** System auto-cleans stale locks. If persists, manually delete:
```bash
rm /workspace/development/saas-bench/sites/{site-name}/locks/bench_new_site.lock
```

#### 5. "Site folder exists and seems partial"
**Cause:** Site directory exists but site isn't installed
**Solution:** API automatically handles with `overwrite=True`, or manually:
```bash
bench drop-site {site-name} --force --no-backup
```

---

## Security Considerations

### 1. Password Management
- Passwords are auto-generated using `secrets.token_urlsafe(16)`
- Stored encrypted in SaaS Company doctype
- Only returned in creation response (not in subsequent API calls)

### 2. Permission Checks
- All APIs validate `frappe.session.user`
- Company access restricted to owner (customer_id) or System Manager
- Subscription validation ensures user owns the subscription

### 3. Database Isolation
- Each site has its own database (e.g., `_acme_corp`)
- MariaDB user scoped to `%` (allows container IPs)
- No cross-site data access

### 4. Site Access Control
- Each site has independent Administrator user
- Admin credentials unique per site
- Site URL follows pattern: `{site-name}.localhost:8000`

---

## Performance Optimization

### 1. Async Company Creation (Future Enhancement)

For production, consider async provisioning:

```python
# Enqueue background job
frappe.enqueue(
    "pix_one.api.companies.create_companies.create_companies_service._provision_site_async",
    company_id=company_doc.name,
    queue="long",
    timeout=600
)
```

### 2. Database Connection Pooling

Configure MariaDB for multi-site:

```ini
# my.cnf
[mysqld]
max_connections = 500
innodb_buffer_pool_size = 2G
```

### 3. Redis Configuration

Use separate Redis DBs for each purpose:

```json
{
    "redis_cache": "redis://redis:6379/0",
    "redis_queue": "redis://redis:6379/1",
    "redis_socketio": "redis://redis:6379/2"
}
```

---

## Monitoring & Maintenance

### 1. Monitor Company Count

```python
# Get subscription usage
subscription = frappe.get_doc("SaaS Subscriptions", subscription_id)
print(f"Companies: {subscription.current_companies}/{plan.max_companies}")
```

### 2. Check Site Health

```bash
# List all sites
bench --site saas.localhost console <<EOF
from pix_one.api.companies.get_companies.get_companies_service import get_companies
print(get_companies())
EOF

# Check specific site
bench --site acme-corp doctor
```

### 3. Database Backup

```bash
# Backup single company site
bench --site acme-corp backup --with-files

# Backup all sites
bench backup-all-sites
```

---

## Frontend Integration

### React Component Example

```jsx
import React, { useState } from 'react';

function CreateCompanyForm() {
    const [formData, setFormData] = useState({
        company_name: '',
        default_currency: 'USD',
        country: 'United States'
    });
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);

        try {
            const response = await frappe.call({
                method: "pix_one.api.companies.create_companies.create_companies_service.create_company",
                args: formData
            });

            if (response.message.success) {
                setResult(response.message.data);
                alert(`Company created! Site: ${response.message.data.site_url}`);
            }
        } catch (error) {
            alert(`Error: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <input
                type="text"
                placeholder="Company Name"
                value={formData.company_name}
                onChange={(e) => setFormData({...formData, company_name: e.target.value})}
                required
            />
            <button type="submit" disabled={loading}>
                {loading ? 'Creating...' : 'Create Company'}
            </button>

            {result && (
                <div className="result">
                    <h3>Company Created Successfully!</h3>
                    <p>Site Name: {result.site_name}</p>
                    <p>Site URL: <a href={result.site_url}>{result.site_url}</a></p>
                    <p>Admin Password: {result.admin_password}</p>
                </div>
            )}
        </form>
    );
}
```

---

## Comparison with Fengine Code

Your fengine code creates **sites** (correct approach), not benches. The main differences:

| Feature | Fengine (Old) | Pix One (New) |
|---------|---------------|---------------|
| Subscription Model | Subscription Payment | SaaS Subscriptions |
| Validation | Basic | Comprehensive (quota, status) |
| Site Tracking | permitted_sites child table | SaaS Company doctype |
| Quota Enforcement | None | Automatic via hooks |
| Error Handling | Basic | Comprehensive with rollback |
| ERPNext Integration | Manual | Automatic Company creation |
| Password Management | Manual | Auto-generated secure |
| Hooks | None | Full lifecycle hooks |
| API Response | Basic | Formatted with ResponseFormatter |

**Recommendation:** Migrate from fengine's approach to this pix_one implementation for:
- Better subscription management
- Automatic quota enforcement
- Comprehensive error handling
- ERPNext integration
- Production-ready architecture

---

## Next Steps

### Immediate:
1. ✅ Test company creation in development
2. ✅ Verify subscription validation works
3. ✅ Test quota enforcement
4. ✅ Test company suspension/activation

### Short-term:
1. ⏳ Implement async provisioning for production
2. ⏳ Add company provisioning progress tracking
3. ⏳ Create frontend dashboard for company management
4. ⏳ Add email notifications on company creation
5. ⏳ Implement company backup/restore functionality

### Long-term:
1. ⏳ Multi-region site deployment
2. ⏳ Custom domain mapping for companies
3. ⏳ Site migration between benches
4. ⏳ Resource usage monitoring per company
5. ⏳ Automated scaling based on usage

---

## Support & Troubleshooting

### Debug Mode

Enable detailed logging:

```python
# In site_config.json
{
    "developer_mode": 1,
    "logging": 2
}
```

### Logs Location

```bash
# Bench logs
tail -f /workspace/development/saas-bench/logs/bench.log

# Site-specific logs
tail -f /workspace/development/saas-bench/sites/acme-corp/logs/web.log
```

### Common Commands

```bash
# List all sites
bench --site saas.localhost console <<EOF
import frappe
print(frappe.get_all("SaaS Company", fields=["company_name", "site_name", "status"]))
EOF

# Drop a failed site
bench drop-site failed-site-name --force --no-backup

# Restart bench
bench restart

# Rebuild if JS changes
bench build
```

---

## Conclusion

This implementation provides a **production-ready, scalable company management system** for your SaaS ERP platform. It follows Frappe best practices, enforces subscription quotas, and provides comprehensive error handling.

**Key Takeaway:** Use **sites for multi-tenancy**, not benches. This is the standard, battle-tested approach used by Frappe Cloud and recommended by the Frappe team.

For questions or issues, refer to the code comments or create an issue in your repository.
