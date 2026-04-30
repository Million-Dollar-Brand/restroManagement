#!/usr/bin/env python3
"""
Test script for multi-tenant restaurant system.
Tests the complete tenant provisioning flow and basic operations.
"""

import asyncio
import httpx
import json
import uuid
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
SUPER_ADMIN_DATA = {
    "email": "admin@restaurantapp.com",
    "username": "superadmin",
    "password": "admin123!",
    "full_name": "Super Admin"
}

RESTAURANT_DATA = {
    "name": "Mario's Italian Kitchen",
    "description": "Authentic Italian cuisine",
    "manager_email": "mario@marioskitchen.com",
    "manager_username": "mario_manager",
    "manager_password": "manager123!",
    "manager_full_name": "Mario Rossi"
}

STAFF_DATA = {
    "email": "anna@marioskitchen.com",
    "username": "anna_waiter",
    "password": "staff123!",
    "full_name": "Anna Smith",
    "role": "waiter"
}

MENU_ITEM_DATA = {
    "name": "Margherita Pizza",
    "description": "Classic tomato, mozzarella, and basil pizza",
    "price": 12.99,
    "category": "Pizza",
    "is_available": True
}

ORDER_DATA = {
    "table_number": 5,
    "items": [
        {
            "menu_item_id": "",  # Will be filled after creating menu item
            "quantity": 2,
            "notes": "Extra cheese please"
        }
    ],
    "notes": "Birthday celebration"
}


class RestaurantAPITester:
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL)
        self.super_admin_token = None
        self.manager_token = None
        self.restaurant_id = None
        self.menu_item_id = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request and return JSON response"""
        response = await self.client.request(method, url, **kwargs)
        if response.status_code >= 400:
            print(f"Error {response.status_code}: {response.text}")
            response.raise_for_status()
        return response.json()

    async def test_super_admin_registration(self):
        """Test super admin registration"""
        print("1. Registering super admin...")
        response = await self.make_request(
            "POST",
            "/api/v1/auth/super-admin/register",
            json=SUPER_ADMIN_DATA
        )
        print(f"✓ Super admin registered: {response['username']}")
        return response

    async def test_super_admin_login(self):
        """Test super admin login"""
        print("2. Super admin login...")
        response = await self.make_request(
            "POST",
            "/api/v1/auth/super-admin/login",
            data={
                "username": SUPER_ADMIN_DATA["username"],
                "password": SUPER_ADMIN_DATA["password"]
            }
        )
        self.super_admin_token = response["access_token"]
        print(f"✓ Super admin logged in, token: {self.super_admin_token[:20]}...")
        return response

    async def test_restaurant_creation(self):
        """Test restaurant creation"""
        print("3. Creating restaurant...")
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        response = await self.make_request(
            "POST",
            "/api/v1/super-admin/restaurants",
            json=RESTAURANT_DATA,
            headers=headers
        )
        self.restaurant_id = response["id"]
        print(f"✓ Restaurant created: {response['name']} (ID: {self.restaurant_id})")
        return response

    async def test_restaurant_manager_login(self):
        """Test restaurant manager login"""
        print("4. Restaurant manager login...")
        response = await self.make_request(
            "POST",
            "/api/v1/auth/restaurant/login",
            data={
                "username": RESTAURANT_DATA["manager_username"],
                "password": RESTAURANT_DATA["manager_password"]
            }
        )
        self.manager_token = response["access_token"]
        print(f"✓ Manager logged in, token: {self.manager_token[:20]}...")
        return response

    async def test_staff_creation(self):
        """Test staff creation"""
        print("5. Creating staff member...")
        headers = {"Authorization": f"Bearer {self.manager_token}"}
        response = await self.make_request(
            "POST",
            "/api/v1/staff",
            json=STAFF_DATA,
            headers=headers
        )
        print(f"✓ Staff created: {response['username']} ({response['role']})")
        return response

    async def test_menu_item_creation(self):
        """Test menu item creation"""
        print("6. Creating menu item...")
        headers = {"Authorization": f"Bearer {self.manager_token}"}
        response = await self.make_request(
            "POST",
            "/api/v1/menu/items",
            json=MENU_ITEM_DATA,
            headers=headers
        )
        self.menu_item_id = response["id"]
        print(f"✓ Menu item created: {response['name']} (${response['price']})")
        return response

    async def test_order_creation(self):
        """Test order creation"""
        print("7. Creating order...")
        # Update order data with menu item ID
        order_data = ORDER_DATA.copy()
        order_data["items"][0]["menu_item_id"] = self.menu_item_id

        headers = {"Authorization": f"Bearer {self.manager_token}"}
        response = await self.make_request(
            "POST",
            "/api/v1/orders",
            json=order_data,
            headers=headers
        )
        print(f"✓ Order created for table {response['table_number']}, total: ${response['total_amount']}")
        return response

    async def test_list_operations(self):
        """Test listing operations"""
        print("8. Testing list operations...")
        headers = {"Authorization": f"Bearer {self.manager_token}"}

        # List staff
        staff = await self.make_request("GET", "/api/v1/staff", headers=headers)
        print(f"✓ Found {len(staff)} staff members")

        # List menu items
        menu = await self.make_request("GET", "/api/v1/menu/items", headers=headers)
        print(f"✓ Found {len(menu)} menu items")

        # List orders
        orders = await self.make_request("GET", "/api/v1/orders", headers=headers)
        print(f"✓ Found {len(orders)} orders")

    async def run_all_tests(self):
        """Run all tests"""
        try:
            print("🚀 Starting Restaurant API Tests\n")

            await self.test_super_admin_registration()
            await self.test_super_admin_login()
            await self.test_restaurant_creation()
            await self.test_restaurant_manager_login()
            await self.test_staff_creation()
            await self.test_menu_item_creation()
            await self.test_order_creation()
            await self.test_list_operations()

            print("\n✅ All tests passed! Multi-tenant system is working correctly.")

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            raise


async def main():
    async with RestaurantAPITester() as tester:
        await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())