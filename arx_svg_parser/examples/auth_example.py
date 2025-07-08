"""
Authentication Example Script

Demonstrates:
- User registration
- Login and token management
- Profile management
- Password changes
- Admin operations
"""

import requests
import json
from typing import Optional

class AuthClient:
    """Client for authentication API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
    
    def _get_headers(self) -> dict:
        """Get headers with authentication token."""
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers
    
    def register_user(self, username: str, email: str, password: str, 
                     full_name: str = None, roles: list = None) -> dict:
        """Register a new user."""
        data = {
            "username": username,
            "email": email,
            "password": password,
            "full_name": full_name,
            "roles": roles or ["viewer"]
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/auth/register",
            json=data
        )
        
        if response.status_code == 200:
            print(f"✅ User '{username}' registered successfully")
            return response.json()
        else:
            print(f"❌ Registration failed: {response.json()}")
            return None
    
    def login(self, username: str, password: str) -> bool:
        """Login user and store tokens."""
        data = {
            "username": username,
            "password": password
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            data=data
        )
        
        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens["access_token"]
            self.refresh_token = tokens["refresh_token"]
            print(f"✅ Login successful for '{username}'")
            return True
        else:
            print(f"❌ Login failed: {response.json()}")
            return False
    
    def refresh_tokens(self) -> bool:
        """Refresh access token using refresh token."""
        if not self.refresh_token:
            print("❌ No refresh token available")
            return False
        
        response = requests.post(
            f"{self.base_url}/api/v1/auth/refresh",
            json={"refresh_token": self.refresh_token}
        )
        
        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens["access_token"]
            self.refresh_token = tokens["refresh_token"]
            print("✅ Tokens refreshed successfully")
            return True
        else:
            print(f"❌ Token refresh failed: {response.json()}")
            return False
    
    def get_profile(self) -> Optional[dict]:
        """Get current user profile."""
        response = requests.get(
            f"{self.base_url}/api/v1/auth/me",
            headers=self._get_headers()
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get profile: {response.json()}")
            return None
    
    def update_profile(self, **kwargs) -> Optional[dict]:
        """Update current user profile."""
        response = requests.put(
            f"{self.base_url}/api/v1/auth/me",
            json=kwargs,
            headers=self._get_headers()
        )
        
        if response.status_code == 200:
            print("✅ Profile updated successfully")
            return response.json()
        else:
            print(f"❌ Profile update failed: {response.json()}")
            return None
    
    def change_password(self, current_password: str, new_password: str) -> bool:
        """Change user password."""
        data = {
            "current_password": current_password,
            "new_password": new_password
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/auth/change-password",
            json=data,
            headers=self._get_headers()
        )
        
        if response.status_code == 200:
            print("✅ Password changed successfully")
            return True
        else:
            print(f"❌ Password change failed: {response.json()}")
            return False
    
    def list_users(self) -> Optional[list]:
        """List all users (admin only)."""
        response = requests.get(
            f"{self.base_url}/api/v1/auth/users",
            headers=self._get_headers()
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to list users: {response.json()}")
            return None
    
    def update_user(self, user_id: str, **kwargs) -> Optional[dict]:
        """Update user (admin only)."""
        response = requests.put(
            f"{self.base_url}/api/v1/auth/users/{user_id}",
            json=kwargs,
            headers=self._get_headers()
        )
        
        if response.status_code == 200:
            print(f"✅ User {user_id} updated successfully")
            return response.json()
        else:
            print(f"❌ User update failed: {response.json()}")
            return None

def main():
    """Main example function."""
    print("🔐 Arxos Authentication Example")
    print("=" * 50)
    
    # Initialize client
    client = AuthClient()
    
    # Example 1: Register users
    print("\n📝 Example 1: User Registration")
    print("-" * 30)
    
    # Register regular user
    user_data = client.register_user(
        username="john_doe",
        email="john@example.com",
        password="securepassword123",
        full_name="John Doe",
        roles=["viewer"]
    )
    
    # Register admin user
    admin_data = client.register_user(
        username="admin_user",
        email="admin@example.com",
        password="adminpassword123",
        full_name="Admin User",
        roles=["admin", "viewer"]
    )
    
    # Example 2: Login and profile management
    print("\n🔑 Example 2: Login and Profile Management")
    print("-" * 40)
    
    # Login as regular user
    if client.login("john_doe", "securepassword123"):
        # Get profile
        profile = client.get_profile()
        if profile:
            print(f"Current user: {profile['username']}")
            print(f"Email: {profile['email']}")
            print(f"Roles: {profile['roles']}")
        
        # Update profile
        updated_profile = client.update_profile(
            full_name="John Smith",
            email="john.smith@example.com"
        )
        
        # Change password
        client.change_password(
            current_password="securepassword123",
            new_password="newsecurepassword456"
        )
    
    # Example 3: Admin operations
    print("\n👑 Example 3: Admin Operations")
    print("-" * 25)
    
    # Login as admin
    if client.login("admin_user", "adminpassword123"):
        # List all users
        users = client.list_users()
        if users:
            print(f"Total users: {len(users)}")
            for user in users:
                print(f"- {user['username']} ({user['email']}) - Roles: {user['roles']}")
        
        # Update a user (if we have user IDs)
        if users and len(users) > 1:
            user_to_update = users[1]  # Second user
            updated_user = client.update_user(
                user_to_update["id"],
                roles=["viewer", "editor"],
                is_active=True
            )
    
    # Example 4: Token refresh
    print("\n🔄 Example 4: Token Refresh")
    print("-" * 20)
    
    # Login again to get fresh tokens
    if client.login("john_doe", "newsecurepassword456"):
        print("Original tokens obtained")
        
        # Simulate token refresh
        if client.refresh_tokens():
            print("Tokens refreshed successfully")
    
    print("\n✅ Authentication example completed!")

def demo_error_handling():
    """Demonstrate error handling scenarios."""
    print("\n🚨 Error Handling Examples")
    print("=" * 30)
    
    client = AuthClient()
    
    # Try to login with wrong password
    print("\n1. Login with wrong password:")
    client.login("john_doe", "wrongpassword")
    
    # Try to access protected endpoint without token
    print("\n2. Access protected endpoint without token:")
    response = requests.get("http://localhost:8000/api/v1/auth/me")
    print(f"Status: {response.status_code}")
    
    # Try to register duplicate user
    print("\n3. Register duplicate user:")
    client.register_user(
        username="john_doe",
        email="duplicate@example.com",
        password="password123"
    )
    
    # Try admin operation without admin role
    print("\n4. Admin operation without admin role:")
    if client.login("john_doe", "newsecurepassword456"):
        users = client.list_users()
        # This should fail due to insufficient permissions

if __name__ == "__main__":
    try:
        main()
        demo_error_handling()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}") 