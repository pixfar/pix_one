"""
Module 4: Payments & Billing - Multi-Gateway Payment Support (Stripe + Razorpay)
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, random_string
from pix_one.common.interceptors.response_interceptors import ResponseFormatter, handle_exceptions


def _get_gateway_config(gateway_name):
    """Get payment gateway configuration from PixOne System Settings."""
    settings = frappe.get_cached_doc("PixOne System Settings", "PixOne System Settings")
    config = {}
    if gateway_name == "stripe":
        config["secret_key"] = settings.get_password("stripe_secret_key") if settings.get("stripe_secret_key") else None
        config["publishable_key"] = settings.get("stripe_publishable_key")
        config["webhook_secret"] = settings.get_password("stripe_webhook_secret") if settings.get("stripe_webhook_secret") else None
    elif gateway_name == "razorpay":
        config["key_id"] = settings.get("razorpay_key_id")
        config["key_secret"] = settings.get_password("razorpay_key_secret") if settings.get("razorpay_key_secret") else None
    return config


def _create_payment_transaction(user, subscription_id, amount, currency, gateway, transaction_type="Initial Payment"):
    """Create a SaaS Payment Transaction record."""
    txn_id = f"TXN-{now_datetime().strftime('%Y%m%d%H%M%S')}-{random_string(6)}"
    txn = frappe.get_doc({
        "doctype": "SaaS Payment Transaction",
        "transaction_id": txn_id,
        "customer_id": user,
        "subscription_id": subscription_id,
        "amount": amount,
        "currency": currency,
        "payment_gateway": gateway,
        "transaction_type": transaction_type,
        "status": "Initiated"
    })
    txn.insert(ignore_permissions=True)
    frappe.db.commit()
    return txn


@frappe.whitelist()
@handle_exceptions
def init_stripe(subscription_id, return_url=None):
    """Initiate a Stripe Checkout payment session."""
    user = frappe.session.user
    sub = frappe.get_doc("SaaS Subscriptions", subscription_id)

    if sub.customer_id != user:
        return ResponseFormatter.forbidden(_("Not your subscription"))

    config = _get_gateway_config("stripe")
    if not config.get("secret_key"):
        return ResponseFormatter.server_error(_("Stripe is not configured"))

    plan = frappe.get_doc("SaaS Subscription Plan", sub.plan_name)

    try:
        import stripe
        stripe.api_key = config["secret_key"]

        # Create transaction record
        txn = _create_payment_transaction(
            user, subscription_id, plan.price, plan.currency, "Stripe"
        )

        base_url = frappe.utils.get_url()
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": plan.currency.lower(),
                    "product_data": {"name": plan.plan_name},
                    "unit_amount": int(plan.price * 100),
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=return_url or f"{base_url}/api/method/pix_one.api.payments.gateway.stripe_gateway.stripe_webhook?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/pixone/payment-cancelled?txn={txn.name}",
            metadata={
                "transaction_id": txn.name,
                "subscription_id": subscription_id,
                "customer_id": user
            }
        )

        txn.db_set("gateway_transaction_id", session.id, update_modified=False)
        frappe.db.commit()

        return ResponseFormatter.success(data={
            "session_id": session.id,
            "checkout_url": session.url,
            "transaction_id": txn.name,
            "publishable_key": config.get("publishable_key")
        })

    except ImportError:
        return ResponseFormatter.server_error(_("Stripe SDK not installed. Run: pip install stripe"))
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Stripe Init Error")
        return ResponseFormatter.server_error(str(e))


@frappe.whitelist(allow_guest=True)
def stripe_webhook(**kwargs):
    """Handle Stripe webhook events."""
    import json
    config = _get_gateway_config("stripe")

    payload = frappe.request.get_data(as_text=True)
    sig_header = frappe.get_request_header("Stripe-Signature")

    try:
        import stripe
        stripe.api_key = config["secret_key"]

        if config.get("webhook_secret") and sig_header:
            event = stripe.Webhook.construct_event(payload, sig_header, config["webhook_secret"])
        else:
            event = json.loads(payload)

        event_type = event.get("type", "")

        if event_type == "checkout.session.completed":
            session = event["data"]["object"]
            metadata = session.get("metadata", {})
            txn_name = metadata.get("transaction_id")
            subscription_id = metadata.get("subscription_id")

            if txn_name and frappe.db.exists("SaaS Payment Transaction", txn_name):
                txn = frappe.get_doc("SaaS Payment Transaction", txn_name)
                txn.status = "Completed"
                txn.gateway_transaction_id = session.get("payment_intent")
                txn.gateway_response = json.dumps(session)
                txn.payment_date = now_datetime()
                txn.save(ignore_permissions=True)

                # Activate subscription
                if subscription_id and frappe.db.exists("SaaS Subscriptions", subscription_id):
                    sub = frappe.get_doc("SaaS Subscriptions", subscription_id)
                    if sub.status in ("Pending Payment", "Draft"):
                        sub.status = "Active"
                        sub.save(ignore_permissions=True)

                frappe.db.commit()

        return {"status": "ok"}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Stripe Webhook Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
@handle_exceptions
def init_razorpay(subscription_id, return_url=None):
    """Initiate a Razorpay payment order."""
    user = frappe.session.user
    sub = frappe.get_doc("SaaS Subscriptions", subscription_id)

    if sub.customer_id != user:
        return ResponseFormatter.forbidden(_("Not your subscription"))

    config = _get_gateway_config("razorpay")
    if not config.get("key_id") or not config.get("key_secret"):
        return ResponseFormatter.server_error(_("Razorpay is not configured"))

    plan = frappe.get_doc("SaaS Subscription Plan", sub.plan_name)

    try:
        import razorpay
        client = razorpay.Client(auth=(config["key_id"], config["key_secret"]))

        txn = _create_payment_transaction(
            user, subscription_id, plan.price, plan.currency, "Razorpay"
        )

        order = client.order.create({
            "amount": int(plan.price * 100),
            "currency": plan.currency,
            "notes": {
                "transaction_id": txn.name,
                "subscription_id": subscription_id
            }
        })

        txn.db_set("gateway_transaction_id", order["id"], update_modified=False)
        frappe.db.commit()

        return ResponseFormatter.success(data={
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "key_id": config["key_id"],
            "transaction_id": txn.name
        })

    except ImportError:
        return ResponseFormatter.server_error(_("Razorpay SDK not installed. Run: pip install razorpay"))
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Razorpay Init Error")
        return ResponseFormatter.server_error(str(e))


@frappe.whitelist(allow_guest=True)
def razorpay_webhook(**kwargs):
    """Handle Razorpay webhook events."""
    import json
    import hmac
    import hashlib

    config = _get_gateway_config("razorpay")
    payload = frappe.request.get_data(as_text=True)
    signature = frappe.get_request_header("X-Razorpay-Signature")

    if config.get("key_secret") and signature:
        expected = hmac.new(
            config["key_secret"].encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            frappe.throw(_("Invalid signature"), frappe.AuthenticationError)

    try:
        event = json.loads(payload)
        event_type = event.get("event", "")

        if event_type == "payment.captured":
            payment = event.get("payload", {}).get("payment", {}).get("entity", {})
            order_id = payment.get("order_id")

            if order_id:
                txn = frappe.get_all(
                    "SaaS Payment Transaction",
                    filters={"gateway_transaction_id": order_id},
                    limit=1
                )
                if txn:
                    txn_doc = frappe.get_doc("SaaS Payment Transaction", txn[0].name)
                    txn_doc.status = "Completed"
                    txn_doc.gateway_response = json.dumps(payment)
                    txn_doc.payment_date = now_datetime()
                    txn_doc.save(ignore_permissions=True)

                    if txn_doc.subscription_id:
                        sub = frappe.get_doc("SaaS Subscriptions", txn_doc.subscription_id)
                        if sub.status in ("Pending Payment", "Draft"):
                            sub.status = "Active"
                            sub.save(ignore_permissions=True)

                    frappe.db.commit()

        return {"status": "ok"}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Razorpay Webhook Error")
        return {"status": "error", "message": str(e)}
