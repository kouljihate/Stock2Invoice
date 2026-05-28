#!/usr/bin/env python3
"""
Script to migrate all collections from local MongoDB stockinvoice database 
to MongoDB Atlas Maure-STC database.
"""

from pymongo import MongoClient
import sys

def migrate_database():
    # Local MongoDB connection
    print("Connecting to local MongoDB...")
    try:
        local_client = MongoClient('mongodb://localhost:27017/')
        local_db = local_client.stockinvoice
        print("[OK] Connected to local MongoDB")
    except Exception as e:
        print(f"[ERROR] Failed to connect to local MongoDB: {e}")
        return False
    
    # Atlas MongoDB connection
    print("Connecting to MongoDB Atlas...")
    atlas_uri = "mongodb+srv://koul:%40LooK9LooK@cluster0.vhxrozb.mongodb.net/Maure-STC?appName=Cluster0"
    try:
        atlas_client = MongoClient(atlas_uri)
        # Test the connection
        atlas_client.admin.command('ping')
        atlas_db = atlas_client['Maure-STC']
        print("[OK] Connected to MongoDB Atlas")
    except Exception as e:
        print(f"[ERROR] Failed to connect to MongoDB Atlas: {e}")
        local_client.close()
        return False
    
    # Get all collection names from local database
    collections = local_db.list_collection_names()
    print(f"\nFound {len(collections)} collections to migrate: {collections}")
    
    # Migrate each collection
    success_count = 0
    for collection_name in collections:
        print(f"\nMigrating collection: {collection_name}")
        
        try:
            # Get local collection
            local_collection = local_db[collection_name]
            
            # Get all documents from local collection
            documents = list(local_collection.find())
            
            if not documents:
                print(f"  [INFO] No documents to migrate (empty collection)")
                success_count += 1
                continue
            
            print(f"  Found {len(documents)} documents to migrate")
            
            # Get Atlas collection
            atlas_collection = atlas_db[collection_name]
            
            # Clear the Atlas collection first (optional - remove if you want to append)
            delete_result = atlas_collection.delete_many({})
            print(f"  Cleared {delete_result.deleted_count} existing documents from Atlas")
            
            # Insert documents into Atlas collection
            if len(documents) <= 1000:
                # For smaller batches, insert all at once
                result = atlas_collection.insert_many(documents)
                print(f"  [OK] Migrated {len(result.inserted_ids)} documents")
            else:
                # For larger batches, insert in chunks to avoid memory issues
                chunk_size = 1000
                migrated_count = 0
                for i in range(0, len(documents), chunk_size):
                    chunk = documents[i:i+chunk_size]
                    result = atlas_collection.insert_many(chunk)
                    migrated_count += len(result.inserted_ids)
                    print(f"  Migrated chunk {i//chunk_size + 1}: {len(result.inserted_ids)} documents")
                print(f"  [OK] Migrated total of {migrated_count} documents")
            
            success_count += 1
            
        except Exception as e:
            print(f"  [ERROR] Failed to migrate collection {collection_name}: {e}")
    
    # Summary
    print(f"\n=== Migration Summary ===")
    print(f"Successfully migrated: {success_count}/{len(collections)} collections")
    
    if success_count == len(collections):
        print("[OK] All collections migrated successfully!")
    else:
        print("[WARNING] Some collections failed to migrate")
    
    # Close connections
    local_client.close()
    atlas_client.close()
    
    return success_count == len(collections)

if __name__ == "__main__":
    print("Starting MongoDB migration from local to Atlas...")
    print("=" * 50)
    
    success = migrate_database()
    
    print("=" * 50)
    if success:
        print("Migration completed successfully!")
        sys.exit(0)
    else:
        print("Migration completed with errors!")
        sys.exit(1)