#!/usr/bin/env python3
import os
import frappe
from pix_one.pix_one.ssl_commerz.payment.command.init_payment import InitPaymentCommand

def test_init_payment():
    """Test init payment command"""
    
    # Absolute path to the site directory
    site_name = "dev.localhost"
    sites_path = "/workspace/development/frappe-bench/sites"
    site_path = os.path.join(sites_path, site_name)
    
    # ✅ Ensure logs folder exists under the correct site path
    os.makedirs(os.path.join(site_path, "logs"), exist_ok=True)
    
    # ✅ Initialize and connect to site using absolute site path
    frappe.init(site=site_name, sites_path=sites_path)
    frappe.connect()


    # Test data
    test_dto = {
        'amount': 100,
        'currency': 'BDT',
        'product_name': 'Test Product',
        'cus_name': 'Test Customer',
        'cus_email': 'test@example.com',
        'cus_phone': '01711111111',
        'cus_add1': 'Dhaka',
        'cus_city': 'Dhaka',
        'cus_country': 'Bangladesh'
    }

    print("🚀 Testing Init Payment...")

    # Execute command
    command = InitPaymentCommand(test_dto, 'Administrator')
    result = command.execute()

    # Check result
    print("\n✅ Result:")
    print(f"Status: {result.get('status')}")
    print(f"Gateway URL: {result.get('GatewayPageURL')}")

    # Check if payment created in database
    payment = frappe.get_all(
        'SSL Payment',
        fields=['name', 'transaction_id', 'amount', 'status'],
        limit=1,
        order_by='creation desc'
    )

    print("\n💾 Payment Created:")
    if payment:
        print(f"Name: {payment[0]['name']}")
        print(f"Transaction ID: {payment[0]['transaction_id']}")
        print(f"Amount: {payment[0]['amount']}")
        print(f"Status: {payment[0]['status']}")
    else:
        print("❌ No payment record found in database.")

    frappe.destroy()
    print("\n🎉 Test completed successfully!")


if __name__ == "__main__":
    test_init_payment()
