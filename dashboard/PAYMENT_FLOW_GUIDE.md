# Complete Payment Flow Implementation Guide

## Overview
This document explains the end-to-end payment flow for the Pix One subscription system with SSLCommerz integration.

## 🔐 Authentication Requirements

**IMPORTANT:** User must be logged in to purchase a plan. The system automatically:
- Fetches customer information from the session user
- Validates subscription ownership
- Ensures secure payment processing

## 📊 Complete Payment Flow

### 1. User Browses Pricing Page

**Frontend:** [PricingCard.jsx](src/pages/Pricing/PricingTiers/PricingCard.jsx)

```javascript
// User clicks "Get Started" button
handlePurchase() {
  // Calls purchasePlan service with only plan_name and app_name
  purchasePlan(call, {
    plan_name: plan.plan_name,
    app_name: 'Pix One'
  })
}
```

### 2. Create Subscription

**Backend API:** `pix_one.api.subscriptions.create.create_subscription`

**What happens:**
- Extracts `customer_id` from `frappe.session.user` (logged-in user)
- Validates the plan exists
- Creates `SaaS Subscriptions` record with:
  - Status: `Pending Payment`
  - Customer: Session user
  - Plan details
  - Calculated dates
  - No license key yet (generated after payment)

**Response:**
```json
{
  "data": {
    "subscription": {
      "name": "SUB-2025-00001",
      "plan_name": "Professional",
      "status": "Pending Payment",
      ...
    }
  }
}
```

### 3. Initiate Payment with Subscription ID Only

**Backend API:** `pix_one.api.payments.init_payment.init_subscription_payment.init_subscription_payment`

**Input:** Only subscription ID
```json
{
  "subscription_id": "SUB-2025-00001"
}
```

**What the backend does automatically:**

1. **Fetch logged-in user:**
   ```python
   current_user = frappe.session.user
   ```

2. **Get subscription details:**
   ```python
   subscription = frappe.get_doc('SaaS Subscriptions', subscription_id)
   ```

3. **Verify ownership:**
   ```python
   if subscription.customer_id != current_user:
       frappe.throw("Unauthorized access")
   ```

4. **Get user details from User doctype:**
   ```python
   user_doc = frappe.get_doc('User', current_user)
   customer_name = user_doc.full_name
   customer_email = user_doc.email
   customer_phone = user_doc.phone or user_doc.mobile_no
   ```

5. **Get plan details:**
   ```python
   plan = frappe.get_doc('SaaS Subscription Plan', subscription.plan_name)
   ```

6. **Calculate total amount:**
   ```python
   total_amount = subscription.price
   if plan.setup_fee and subscription.status == 'Pending Payment':
       total_amount += plan.setup_fee
   ```

7. **Prepare SSLCommerz payment data:**
   ```python
   post_body = {
       'total_amount': total_amount,
       'currency': subscription.currency or 'BDT',
       'tran_id': generate_transaction_id(),  # Auto-generated
       'success_url': f"{site_url}/api/method/.../payment_success",
       'fail_url': f"{site_url}/api/method/.../payment_fail",
       'cancel_url': f"{site_url}/api/method/.../payment_cancel",
       'cus_name': customer_name,  # From session user
       'cus_email': customer_email,  # From session user
       'cus_phone': customer_phone,  # From session user
       'cus_add1': 'Dhaka',  # Default or from user profile
       'cus_city': 'Dhaka',
       'cus_country': 'Bangladesh',
       'product_name': f"{plan.plan_name} - {subscription.billing_interval}",
       'product_category': 'Subscription',
       'value_a': subscription_id,  # Pass subscription context
       'value_b': plan.plan_name,
       'value_c': current_user,
       'value_d': transaction_type  # Initial/Recurring/Renewal
   }
   ```

8. **Create SSLCommerz session:**
   ```python
   response = sslcz.createSession(post_body)
   ```

9. **Create Payment Transaction record:**
   ```python
   frappe.get_doc({
       'doctype': 'SaaS Payment Transaction',
       'transaction_id': tran_id,
       'subscription_id': subscription_id,
       'customer_id': current_user,
       'status': 'Initiated',
       ...
   }).insert()
   ```

**Response:**
```json
{
  "status": "success",
  "data": {
    "gateway_url": "https://sandbox.sslcommerz.com/EasyCheckOut/...",
    "transaction_id": "TXN-73E585CCF96D",
    "session_key": "...",
    "subscription_id": "SUB-2025-00001"
  }
}
```

### 4. Redirect to SSLCommerz

**Frontend:**
```javascript
// From purchasePlan service
if (result.paymentUrl) {
  window.location.href = result.paymentUrl;
}
```

User is now at SSLCommerz payment page where they complete payment.

### 5. Payment Success Callback

**SSLCommerz calls:** `pix_one.api.payments.payment_success.payment_success_service.payment_success`

**What happens:**

1. **Receive payment data from SSLCommerz:**
   ```python
   payment_data = frappe.local.form_dict
   tran_id = payment_data.get('tran_id')
   val_id = payment_data.get('val_id')
   amount = payment_data.get('amount')
   subscription_id = payment_data.get('value_a')  # Retrieved from init
   ```

2. **Validate transaction with SSLCommerz:**
   ```python
   validation_response = sslcz.validationTransactionOrder(val_id)
   if validation_response.get('status') != 'VALID':
       return failure_response
   ```

3. **Create/Update Payment Transaction:**
   ```python
   payment_transaction = frappe.get_doc({
       'doctype': 'SaaS Payment Transaction',
       'transaction_id': tran_id,
       'subscription_id': subscription_id,
       'status': 'Completed',
       'gateway_transaction_id': bank_tran_id,
       ...
   }).insert()
   ```

4. **Activate Subscription:**
   ```python
   subscription = frappe.get_doc('SaaS Subscriptions', subscription_id)
   subscription.status = 'Active'
   subscription.start_date = nowdate()
   subscription.end_date = calculate_end_date()
   subscription.total_amount_paid += amount
   ```

5. **Generate License Key:**
   ```python
   subscription.license_key = f"LIC-{uuid.uuid4().hex[:16].upper()}"
   ```

6. **Create License Validation Record:**
   ```python
   frappe.get_doc({
       'doctype': 'SaaS App Validation',
       'license_key': subscription.license_key,
       'subscription_id': subscription.name,
       'customer_id': customer_id,
       'validation_status': 'Active',
       'max_users': plan.max_users,
       'max_storage_mb': plan.max_storage_mb,
       ...
   }).insert()
   ```

7. **Redirect to frontend success page:**
   ```python
   return {
       'status': 'success',
       'redirect_url': f"{site_url}/pixone/payment/success?subscription={subscription_id}"
   }
   ```

### 6. Display Success Page

**Frontend:** [PaymentSuccess.jsx](src/pages/Payment/PaymentSuccess.jsx)

**What it shows:**
- ✅ Success animation
- Subscription details (plan, dates, amount paid)
- License key with copy button
- Next steps instructions
- Auto-redirect to subscription details in 10 seconds

**What it does:**
```javascript
// Parse subscription ID from URL
const subscriptionId = searchParams.get('subscription');

// Fetch subscription details
const { data } = useQuery({
  queryKey: [QUERY_KEYS.SUBSCRIPTION_DETAILS, subscriptionId],
  queryFn: () => getSubscriptionDetails(call, subscriptionId)
});

// Show subscription info and license key
// Auto-redirect after countdown
```

### 7. Payment Failed Flow

**SSLCommerz calls:** `pix_one.api.payments.payment_fail.payment_fail_service.payment_fail`

**Backend:**
1. Creates failed transaction record
2. Updates subscription status to `Past Due` or keeps in `Pending Payment`
3. Redirects to: `/pixone/payment/failed?transaction={tran_id}&reason={reason}`

**Frontend:** [PaymentFailed.jsx](src/pages/Payment/PaymentFailed.jsx)
- Shows error message with context
- Suggests solutions based on failure reason
- Provides retry button
- Contact support option

### 8. Payment Cancelled Flow

**SSLCommerz calls:** `pix_one.api.payments.payment_cancel.payment_cancel_service.payment_cancel`

**Backend:**
1. Creates cancelled transaction record
2. Keeps subscription in `Pending Payment` status
3. Redirects to: `/pixone/payment/cancelled?transaction={tran_id}`

**Frontend:** [PaymentCancelled.jsx](src/pages/Payment/PaymentCancelled.jsx)
- Explains cancellation
- Offers to retry payment
- Auto-redirects to pricing in 15 seconds

## 🔄 Renewal Flow

When user clicks "Renew" on expired/expiring subscription:

```javascript
// Frontend
renewSubscription(call, subscriptionId)

// Backend
init_subscription_payment(subscription_id)
// Same flow as new purchase
// Automatically detects it's a renewal
// Updates transaction_type to 'Renewal'
```

## 📝 Key Security Features

1. **Session-based authentication:** All customer info from logged-in user
2. **Ownership verification:** Backend checks subscription belongs to current user
3. **Payment validation:** SSLCommerz validation before activating subscription
4. **No client-side secrets:** All sensitive operations on backend
5. **Transaction logging:** Every step logged for audit trail

## 🎯 Frontend Service Usage

### For New Purchase:
```javascript
import { purchasePlan } from '@/services/subscription.service';

const result = await purchasePlan(call, {
  plan_name: 'Professional',
  app_name: 'Pix One'
});

window.location.href = result.paymentUrl;
```

### For Renewal:
```javascript
import { renewSubscription } from '@/services/subscription.service';

const result = await renewSubscription(call, subscriptionId);
window.location.href = result.paymentUrl;
```

## 🔧 Backend API Reference

### Init Subscription Payment
**Endpoint:** `pix_one.api.payments.init_payment.init_subscription_payment.init_subscription_payment`

**Method:** POST

**Authentication:** Required (logged-in user)

**Request:**
```json
{
  "subscription_id": "SUB-2025-00001"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "gateway_url": "https://sandbox.sslcommerz.com/...",
    "transaction_id": "TXN-...",
    "session_key": "...",
    "subscription_id": "SUB-2025-00001"
  }
}
```

**What it does:**
- ✅ Fetches customer info from session user automatically
- ✅ Gets subscription and plan details
- ✅ Calculates total amount (price + setup fee)
- ✅ Creates payment transaction record
- ✅ Initiates SSLCommerz session
- ✅ Returns gateway URL for redirect

**Error Handling:**
- Throws if user not logged in
- Throws if subscription doesn't belong to user
- Throws if subscription status doesn't allow payment
- Throws if SSLCommerz session creation fails

## 🌐 SSLCommerz Webhooks

### Success Webhook
- **URL:** `/api/method/pix_one.api.payments.payment_success.payment_success_service.payment_success`
- **Validates payment** with SSLCommerz
- **Activates subscription**
- **Generates license key**
- **Creates license validation**
- **Redirects to:** `/pixone/payment/success?subscription={id}`

### Fail Webhook
- **URL:** `/api/method/pix_one.api.payments.payment_fail.payment_fail_service.payment_fail`
- **Creates failed transaction**
- **Updates subscription to Past Due**
- **Redirects to:** `/pixone/payment/failed?transaction={id}&reason={reason}`

### Cancel Webhook
- **URL:** `/api/method/pix_one.api.payments.payment_cancel.payment_cancel_service.payment_cancel`
- **Creates cancelled transaction**
- **Keeps subscription pending**
- **Redirects to:** `/pixone/payment/cancelled?transaction={id}`

## 📱 User Journey

```
1. User browses pricing page (public)
   ↓
2. Clicks "Get Started" (must be logged in)
   ↓
3. System creates subscription (Pending Payment)
   ↓
4. System initiates payment (fetches user info automatically)
   ↓
5. Redirects to SSLCommerz
   ↓
6. User completes payment on SSLCommerz
   ↓
7. SSLCommerz calls webhook
   ↓
8. System validates & activates subscription
   ↓
9. Generates license key
   ↓
10. Redirects to success page
   ↓
11. Shows subscription details & license
   ↓
12. Auto-redirects to subscription management
```

## ✅ Testing Checklist

- [ ] User can browse pricing without login
- [ ] Purchase requires login
- [ ] Customer info fetched from session automatically
- [ ] Subscription created with Pending Payment status
- [ ] Payment initiated with correct user details
- [ ] Redirect to SSLCommerz works
- [ ] Payment success activates subscription
- [ ] License key generated and displayed
- [ ] Success page shows correct details
- [ ] Payment failure shows appropriate error
- [ ] Payment cancellation allows retry
- [ ] Renewal flow works for expired subscriptions
- [ ] Unauthorized access blocked (different user's subscription)

## 🚀 Production Deployment

1. **Configure SSLCommerz:**
   - Set production credentials in PixOne System Settings
   - Disable sandbox mode
   - Ensure HTTPS enabled

2. **Verify Webhooks:**
   - Test all three callbacks (success, fail, cancel)
   - Ensure site URL is accessible from internet
   - Check callback URLs in SSLCommerz dashboard

3. **Enable Scheduler:**
   - Verify scheduled tasks running
   - Test expiry reminders
   - Test auto-renewal processing

4. **Monitor:**
   - Check error logs regularly
   - Monitor transaction success rate
   - Track subscription lifecycle events

---

**Last Updated:** 2025-11-30
**Version:** 2.0.0 (Simplified Payment Flow)
