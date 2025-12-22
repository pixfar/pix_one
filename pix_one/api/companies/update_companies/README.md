# Company Update Service

This service handles updating company details and renaming sites with proper security measures.

## API Endpoints

### 1. Update Basic Company Details

Update non-critical company information without password verification.

```bash
POST /api/method/pix_one.api.companies.update_companies.update_companies_service.update_company_basic
```

**Request:**
```json
{
  "company_id": "COMP-2025-00001",
  "company_name": "Updated Company Name",
  "admin_email": "newemail@example.com",
  "default_currency": "EUR",
  "country": "Germany"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Company updated successfully",
  "data": {
    "company_id": "COMP-2025-00001",
    "updated_fields": {
      "company_name": "Updated Company Name",
      "admin_email": "newemail@example.com"
    },
    "company_name": "Updated Company Name",
    "admin_email": "newemail@example.com",
    "default_currency": "EUR",
    "country": "Germany"
  }
}
```

**Updatable Fields:**
- `company_name` - Company display name
- `admin_email` - Administrator email for the site
- `default_currency` - Default currency code
- `country` - Country name

### 2. Update Site Domain (Rename Site)

Update the site domain/name. **Requires user password for security.**

```bash
POST /api/method/pix_one.api.companies.update_companies.update_companies_service.update_site_domain
```

**Request:**
```json
{
  "company_id": "COMP-2025-00001",
  "new_domain": "newsite.localhost",
  "user_password": "your_password"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Site domain successfully updated from 'oldsite.localhost' to 'newsite.localhost'",
  "data": {
    "company_id": "COMP-2025-00001",
    "company_name": "Acme Corporation",
    "old_site_name": "oldsite.localhost",
    "new_site_name": "newsite.localhost",
    "site_url": "http://newsite.localhost",
    "status": "Active",
    "site_status": "Active"
  }
}
```

**Response (Invalid Password):**
```json
{
  "success": false,
  "message": "Invalid user password",
  "error_code": "VALIDATION_ERROR",
  "errors": {
    "user_password": "INVALID_PASSWORD"
  }
}
```

## How Site Renaming Works

### Security Requirements
1. **User Password Required** - Must provide the logged-in user's password
2. **Password Verification** - Password is verified against the current user's account before renaming
3. **Active Sites Only** - Only sites with status "Active" can be renamed
4. **Company Ownership** - User must be the owner of the company (customer_id match)

### Renaming Process
1. Validates the company exists and user has permission
2. Checks the site status is "Active"
3. Verifies the logged-in user's password
4. Checks if the new site name doesn't already exist
5. Updates site_status to "Renaming"
6. Executes `bench rename-site` command (using site's admin password from company doc)
7. Updates company document with new site details
8. Adds rename note to provisioning_notes

### What Gets Updated
- `domain` - New domain value
- `site_name` - New site name
- `db_name` - New database name (prefixed with underscore)
- `site_status` - Set back to "Active" after successful rename
- `provisioning_notes` - Appends rename history

### Database Changes
The rename operation:
- Renames the site directory
- Renames the database
- Updates all site configuration files
- Updates nginx configuration (if applicable)

## Error Codes

### VALIDATION_ERROR
- `INVALID_PASSWORD` - Administrator password is incorrect
- `SITE_EXISTS` - New site name already exists
- `INVALID_OR_INACTIVE` - Subscription is not active

### SERVER_ERROR
- `SITE_RENAME_FAILED` - Technical error during site rename

## Security Notes

1. **Password Protection** - Site renaming requires Administrator password to prevent unauthorized changes
2. **User Verification** - Only the company owner (customer_id) can update the company
3. **Subscription Check** - Active subscription required for all updates
4. **Audit Trail** - All renames are logged in provisioning_notes with timestamp

## Restrictions

1. **Status Requirement** - Site must be "Active" to be renamed
2. **Unique Names** - New site name must be unique across the system
3. **No Empty Values** - Domain and password cannot be empty
4. **Subscription** - Active subscription required

## Example Usage

### Update Company Name Only
```bash
curl -X POST "{{PIXONE_BASE_URL}}/api/method/pix_one.api.companies.update_companies.update_companies_service.update_company_basic" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "COMP-2025-00001",
    "company_name": "New Company Name"
  }'
```

### Rename Site Domain
```bash
curl -X POST "{{PIXONE_BASE_URL}}/api/method/pix_one.api.companies.update_companies.update_companies_service.update_site_domain" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "COMP-2025-00001",
    "new_domain": "newdomain.localhost",
    "admin_password": "your_secure_password"
  }'
```

## Best Practices

1. **Test First** - Test domain renaming in a development environment first
2. **Backup** - Always have backups before renaming sites
3. **Communication** - Inform users before changing the site domain
4. **DNS Updates** - Update DNS records if using custom domains
5. **Update Links** - Update any hardcoded links to the old domain
