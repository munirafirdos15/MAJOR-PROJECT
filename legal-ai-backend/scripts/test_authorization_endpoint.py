import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"


async def test_authorization():
    """Test the authorization system."""
    
    async with httpx.AsyncClient() as client:
        # Step 1: Login to get access token
        print("1. Logging in with User account...")
        login_response = await client.post(
            f"{BASE_URL}/api/login",
            json={
                "username": "testuser",
                "password": "TestPassword123!"
            }
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(login_response.text)
            return
        
        login_data = login_response.json()
        access_token = login_data.get("access_token")
        print(f"✅ Login successful. Access token: {access_token[:20]}...")
        
        # Step 2: Test with document.view permission (should succeed)
        print("\n2. Testing /api/test/document (should have document.view permission)...")
        headers = {"Authorization": f"Bearer {access_token}"}
        
        response = await client.get(
            f"{BASE_URL}/api/test/document",
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"✅ Success! Response: {response.json()}")
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(response.text)
        
        print("\n" + "="*60)
        print("Authorization test completed!")


if __name__ == "__main__":
    asyncio.run(test_authorization())
