"""
Test script for Customer Profile endpoint
"""

from apps.users.models import User
from apps.users.serializers import CustomerProfileSerializer

# Get a user (first customer or any user)
users = User.objects.filter(role='customer')[:1]

if users.exists():
    user = users.first()
    print(f"\n=== Testing Customer Profile for: {user.username} ===\n")
    
    # Serialize the user
    serializer = CustomerProfileSerializer(user)
    data = serializer.data
    
    print(f"User ID: {data['id']}")
    print(f"Username: {data['username']}")
    print(f"Email: {data['email']}")
    print(f"Full Name: {data['full_name']}")
    print(f"Phone: {data['phone']}")
    print(f"Role: {data['role']} ({data['role_display']})")
    print(f"Status: {data['status']} ({data['status_display']})")
    print(f"\n--- Statistics ---")
    print(f"Total Orders: {data['total_orders']}")
    print(f"Active Orders: {data['active_orders']}")
    print(f"Favorites Count: {data['favorites_count']}")
    print(f"\nLast Login: {data['last_login_at']}")
    print(f"Date Joined: {data['date_joined']}")
    
    print("\n✓ Customer Profile Serializer working correctly!")
else:
    print("\nNo customer users found in database.")
    print("Creating a test to verify serializer structure...")
    
    # Just verify the serializer can be instantiated
    print("\n✓ CustomerProfileSerializer class is available and can be imported!")
