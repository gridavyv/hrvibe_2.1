#!/usr/bin/env python3
"""
Get Manager by ID from database
Usage: python3 local_db_setup/get_manager.py <manager_id>
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from database import SessionLocal, Manager

def get_manager_by_id(manager_id):
    """Get manager by ID"""
    db = SessionLocal()
    
    try:
        manager = db.query(Manager).filter(Manager.id == manager_id).first()
        
        if manager:
            print("=" * 60)
            print(f"✅ Found Manager (ID: {manager_id})")
            print("=" * 60)
            print(f"ID:                          {manager.id}")
            print(f"Username:                    {manager.username or 'N/A'}")
            print(f"First Name:                  {manager.first_name or 'N/A'}")
            print(f"Last Name:                   {manager.last_name or 'N/A'}")
            print(f"Privacy Policy Confirmed:    {manager.privacy_policy_confirmed}")
            print(f"Access Token Received:        {manager.access_token_recieved}")
            print(f"First Time Seen:             {manager.first_time_seen}")
            print(f"Created At:                  {manager.created_at}")
            print(f"Updated At:                  {manager.updated_at}")
            
            if manager.hh_data:
                print(f"\nHH Data (JSON):")
                import json
                print(json.dumps(manager.hh_data, indent=2, ensure_ascii=False))
            
            return manager
        else:
            print(f"❌ Manager with ID {manager_id} not found")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 local_db_setup/get_manager.py <manager_id>")
        print("\nExample:")
        print("  python3 local_db_setup/get_manager.py 123456789")
        sys.exit(1)
    
    try:
        manager_id = int(sys.argv[1])
        get_manager_by_id(manager_id)
    except ValueError:
        print(f"❌ Error: '{sys.argv[1]}' is not a valid ID (must be a number)")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
