# Company Provisioning Service

This service handles asynchronous provisioning of company sites with email notifications.

## How It Works

### 1. Create Company (Immediate Response)
When a user creates a company via the API:
```bash
POST /api/method/pix_one.api.companies.create_companies.create_companies_service.create_company
```

**Request:**
```json
{
  "company_name": "Acme Corporation",
  "company_abbr": "ACME",
  "admin_password": "secure_password",
  "admin_email": "admin@acme.com",
  "default_currency": "USD",
  "country": "United States",
  "domain": "acme.localhost"
}
```

**Immediate Response (Status: 201):**
```json
{
  "success": true,
  "message": "Company 'Acme Corporation' created. Provisioning in progress...",
  "data": {
    "company_id": "COMP-2025-00001",
    "company_name": "Acme Corporation",
    "site_name": "acme.localhost",
    "site_url": "http://acme.localhost",
    "status": "Queued",
    "message": "Company record created. Site provisioning has been queued and will be processed shortly. You will receive an email with login credentials once provisioning is complete."
  }
}
```

### 2. Background Processing
The site provisioning happens in the background:
1. Creates a Frappe site
2. Installs requested apps (e.g., erpnext)
3. Updates company status progressively:
   - `Queued` → `Provisioning` → `Active` (or `Failed`)

### 3. Email Notification
Once provisioning completes, the customer receives an email at their registered email address (the user who created the company).

#### Success Email
- **Sent to:** Customer's email (current logged-in user)
- **Subject:** "Your Site is Ready: Acme Corporation"
- **Contents:**
  - Site URL with clickable link
  - Admin credentials (admin_email & admin_password for site login)
  - Next steps to get started
  - Security reminder to change password

**Note:** The email contains the site administrator credentials (`admin_email` and `admin_password`), which may be different from the customer's email address.

#### Failure Email
- **Sent to:** Customer's email (current logged-in user)
- **Subject:** "Site Provisioning Failed: Acme Corporation"
- **Contents:**
  - Error details
  - Support reference ID (Company ID)
  - Contact information for support

## API Endpoints

### Check Provisioning Status
```bash
GET /api/method/pix_one.api.companies.create_companies.create_companies_service.get_company_status?company_id=COMP-2025-00001
```

**Response:**
```json
{
  "success": true,
  "data": {
    "company_id": "COMP-2025-00001",
    "company_name": "Acme Corporation",
    "status": "Active",
    "site_status": "Active",
    "site_name": "acme.localhost",
    "site_url": "http://acme.localhost",
    "provisioning_started_at": "2025-01-15 10:30:00",
    "provisioning_completed_at": "2025-01-15 10:35:00",
    "provisioning_notes": "Site created successfully\nApps: Installed apps: erpnext"
  }
}
```

## Status Flow

```
Draft → Queued → Provisioning → Active
                              ↘ Failed
```

- **Draft**: Company record created, not yet queued
- **Queued**: Background job queued, waiting to start
- **Provisioning**: Site creation in progress
- **Active**: Site successfully provisioned and ready
- **Failed**: Provisioning failed (can be retried)

## Background Job Configuration

The provisioning job uses:
- **Queue:** `long` (for time-consuming tasks)
- **Timeout:** 600 seconds (10 minutes)
- **Function:** `pix_one.api.companies.create_companies.provisioning_jobs.provision_company_site`

## Email Configuration

Emails are sent using Frappe's built-in email system. Ensure your site has:
1. Email account configured in Email Account doctype
2. SMTP settings properly configured
3. Default outgoing email set

## Monitoring

To monitor background jobs:
```bash
# View background jobs
bench --site <site> background-jobs

# View logs
tail -f frappe-bench/logs/worker.*.log
```

## Error Handling

If provisioning fails:
1. Company status is set to `Failed`
2. Error details are logged in `provisioning_notes`
3. Customer receives a failure email
4. Error is logged in Frappe Error Log

## Security Notes

- Admin passwords are sent only once via email
- Passwords are stored encrypted in the SaaS Company doctype
- Customers should change passwords after first login
- Email transmission should use TLS/SSL
