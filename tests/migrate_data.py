import os
from pymongo import MongoClient
import certifi

# Local MongoDB connection
local_client = MongoClient('mongodb://localhost:27017/')
local_db = local_client.stockinvoice

# Atlas MongoDB connection
atlas_uri = "mongodb+srv://koul:%3C%40LooK9LooK%3E@cluster0.vhxrozb.mongodb.net/Maure-STC?appName=Cluster0"
atlas_client = MongoClient(atlas_uri, 
                          tlsAllowInvalidCertificates=True,
                          tlsAllowInvalidHostnames=True)
atlas_db = atlas_client['Maure-STC']

# Get all collection names from local database
collections = local_db.list_collection_names()

print(f"Found {len(collections)} collections to migrate: {collections}")

# Migrate each collection
for collection_name in collections:
    print(f"Migrating collection: {collection_name}")
    
    # Get all documents from local collection
    local_collection = local_db[collection_name]
    documents = list(local_collection.find())
    
    if documents:
        # Clear the atlas collection first
        atlas_collection = atlas_db[collection_name]
        atlas_collection.delete_many({})
        
        # Insert documents into atlas collection
        result = atlas_collection.insert_many(documents)
        print(f"  Migrated {len(result.inserted_ids)} documents")
    else:
        print("  No documents to migrate")

print("Migration completed!")

# Close connections
local_client.close()
atlas_client.close()