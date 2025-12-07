# API Endpoints Reference

## Correct Endpoint Paths

This document lists all API endpoints with their correct paths based on the actual file structure.

### Pattern
`pix_one.api.{module}.{directory}.{filename}.{function_name}`

## Subscription & Pricing Endpoints

| Endpoint | Path | File Location |
|----------|------|---------------|
| GET_PLANS | `pix_one.api.subscription_plans.get_plans.get_plans.get_subscription_plans` | `pix_one/api/subscription_plans/get_plans/get_plans.py` |
| CREATE_SUBSCRIPTION | `pix_one.api.subscriptions.create.create_subscription.create_subscription` | `pix_one/api/subscriptions/create/create_subscription.py` |
| GET_MY_SUBSCRIPTIONS | `pix_one.api.subscriptions.list.get_subscriptions.get_my_subscriptions` | `pix_one/api/subscriptions/list/get_subscriptions.py` |
| GET_SUBSCRIPTION | `pix_one.api.subscriptions.get.get_subscription.get_subscription` | `pix_one/api/subscriptions/get/get_subscription.py` |
| GET_SUBSCRIPTION_STATS | `pix_one.api.subscriptions.list.get_subscriptions.get_subscription_stats` | `pix_one/api/subscriptions/list/get_subscriptions.py` |
| CANCEL_SUBSCRIPTION | `pix_one.api.subscriptions.cancel.cancel_subscription.cancel_subscription` | `pix_one/api/subscriptions/cancel/cancel_subscription.py` |
| REACTIVATE_SUBSCRIPTION | `pix_one.api.subscriptions.cancel.cancel_subscription.reactivate_subscription` | `pix_one/api/subscriptions/cancel/cancel_subscription.py` |
| INITIATE_PAYMENT | `pix_one.api.subscriptions.create.create_subscription.initiate_subscription_payment` | `pix_one/api/subscriptions/create/create_subscription.py` |

## Payment Endpoints

| Endpoint | Path | File Location |
|----------|------|---------------|
| INITIATE | `pix_one.api.payments.init_payment.init_payment_service.initiate_payment` | `pix_one/api/payments/init_payment/init_payment_service.py` |
| INITIATE_SUBSCRIPTION | `pix_one.api.payments.init_payment.init_subscription_payment.init_subscription_payment` | `pix_one/api/payments/init_payment/init_subscription_payment.py` |
| SUCCESS | `pix_one.api.payments.payment_success.payment_success_service.payment_success` | `pix_one/api/payments/payment_success/payment_success_service.py` |
| CANCEL | `pix_one.api.payments.payment_cancel.payment_cancel_service.payment_cancel` | `pix_one/api/payments/payment_cancel/payment_cancel_service.py` |
| FAIL | `pix_one.api.payments.payment_fail.payment_fail_service.payment_fail` | `pix_one/api/payments/payment_fail/payment_fail_service.py` |

## Transaction Endpoints

| Endpoint | Path | File Location |
|----------|------|---------------|
| GET_MY_TRANSACTIONS | `pix_one.api.transactions.get_transactions.get_my_transactions` | `pix_one/api/transactions/get_transactions.py` |
| GET_TRANSACTION | `pix_one.api.transactions.get_transactions.get_transaction` | `pix_one/api/transactions/get_transactions.py` |
| GET_TRANSACTION_STATS | `pix_one.api.transactions.get_transactions.get_transaction_stats` | `pix_one/api/transactions/get_transactions.py` |
| GET_SUBSCRIPTION_TRANSACTIONS | `pix_one.api.transactions.get_transactions.get_subscription_transactions` | `pix_one/api/transactions/get_transactions.py` |

## License Endpoints

| Endpoint | Path | File Location |
|----------|------|---------------|
| VALIDATE | `pix_one.api.license.validate_license` | `pix_one/api/license/validate_license.py` |
| CHECK_STATUS | `pix_one.api.license.check_license_status` | `pix_one/api/license/check_license_status.py` |
| UPDATE_USAGE | `pix_one.api.license.update_license_usage` | `pix_one/api/license/update_license_usage.py` |
| GET_DETAILS | `pix_one.api.license.get_license_details` | `pix_one/api/license/get_license_details.py` |

## How to Find Correct Path

1. **Locate the file:**
   ```bash
   find pix_one/api -name "your_file.py"
   ```

2. **Check the function name:**
   ```bash
   grep "@frappe.whitelist" pix_one/api/path/to/file.py
   ```

3. **Build the path:**
   ```
   pix_one.api.{folder1}.{folder2}.{filename_without_py}.{function_name}
   ```

## Example

For file: `pix_one/api/subscription_plans/get_plans/get_plans.py`
With function: `get_subscription_plans()`

Path becomes:
```
pix_one.api.subscription_plans.get_plans.get_plans.get_subscription_plans
         │              │          │        │              │
         └─module       └─folder1  └─folder2 └─filename    └─function
```

## Common Mistakes

❌ **Wrong:** `pix_one.api.subscription_plans.get_plans.get_subscription_plans`
- Missing the filename `get_plans` before function name

✅ **Correct:** `pix_one.api.subscription_plans.get_plans.get_plans.get_subscription_plans`
- Includes both directory AND filename

---

**Last Updated:** 2025-11-30
