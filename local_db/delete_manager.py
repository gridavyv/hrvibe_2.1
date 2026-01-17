#!/usr/bin/env python3
"""
Delete Manager by ID from database
Usage: python3 local_db/delete_manager.py <manager_id> [--confirm]
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from database import SessionLocal, Managers

def delete_manager_by_id(manager_id, confirm=False):
    """Delete manager by ID"""
    db = SessionLocal()
    
    try:
        # First, check if manager exists
        manager = db.query(Managers).filter(Managers.id == manager_id).first()
        
        if not manager:
            print(f"❌ Manager with ID {manager_id} not found")
            return False
        
        # Display manager info before deletion
        print("=" * 60)
        print(f"⚠️  Manager to be deleted (ID: {manager_id})")
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
        print("=" * 60)
        
        # Confirm deletion
        if not confirm:
            response = input("\n⚠️  Are you sure you want to delete this manager? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("❌ Deletion cancelled")
                return False
        
        # Delete the manager
        db.delete(manager)
        db.commit()
        
        print(f"\n✅ Manager with ID {manager_id} has been successfully deleted")
        return True
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 local_db/delete_manager.py <manager_id> [--confirm]")
        print("\nOptions:")
        print("  <manager_id>    The ID of the manager to delete (must be a number)")
        print("  --confirm       Skip confirmation prompt")
        print("\nExample:")
        print("  python3 local_db/delete_manager.py 123456789")
        print("  python3 local_db/delete_manager.py 123456789 --confirm")
        sys.exit(1)
    
    try:
        manager_id = int(sys.argv[1])
        confirm = '--confirm' in sys.argv
        
        success = delete_manager_by_id(manager_id, confirm=confirm)
        sys.exit(0 if success else 1)
        
    except ValueError:
        print(f"❌ Error: '{sys.argv[1]}' is not a valid ID (must be a number)")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n❌ Deletion cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
