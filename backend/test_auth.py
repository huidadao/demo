"""Test script for authentication flow."""

import asyncio
import requests

BASE_URL = "http://127.0.0.1:8000"


def test_auth_flow():
    print("=" * 50)
    print("🧪 Authentication Flow Test")
    print("=" * 50)

    # Test 1: Register a new user
    print("\n1️⃣ Test: Register User")
    print("-" * 30)
    register_data = {"email": "testuser@example.com", "password": "password123"}
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    # Test 2: Login with registered user
    print("\n2️⃣ Test: Login")
    print("-" * 30)
    login_data = {"email": "testuser@example.com", "password": "password123"}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")
        print(f"✅ Login successful!")
        print(f"   Token: {access_token[:50]}...")
    else:
        print(f"❌ Login failed: {response.json()}")
        return

    # Test 3: Get current user with token
    print("\n3️⃣ Test: Get Current User (Protected Route)")
    print("-" * 30)
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    # Test 4: Try without token (should fail)
    print("\n4️⃣ Test: Get Current User WITHOUT Token")
    print("-" * 30)
    response = requests.get(f"{BASE_URL}/auth/me")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    # Test 5: Try with invalid token (should fail)
    print("\n5️⃣ Test: Get Current User with INVALID Token")
    print("-" * 30)
    headers = {"Authorization": "Bearer invalid_token_here"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    # Test 6: Login with wrong password
    print("\n6️⃣ Test: Login with Wrong Password")
    print("-" * 30)
    login_data = {"email": "testuser@example.com", "password": "wrongpassword"}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    print("=" * 50)


if __name__ == "__main__":
    test_auth_flow()
