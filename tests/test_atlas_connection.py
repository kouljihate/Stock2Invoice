from pymongo import MongoClient
import certifi

# Corrected connection string with proper URL encoding for @ in password
uri = "mongodb+srv://koul:%40LooK9LooK@cluster0.vhxrozb.mongodb.net/Maure-STC?appName=Cluster0"

print("Testing connection to MongoDB Atlas...")
print(f"URI: {uri}")

try:
    # Try with certificate validation first
    client = MongoClient(uri, tlsCAFile=certifi.where())
    # Ping the server to confirm connection
    client.admin.command('ping')
    print("SUCCESS: Connected to MongoDB Atlas with certificate validation!")
    
    # List databases to verify access
    dbs = client.list_database_names()
    print(f"Available databases: {dbs}")
    
    # Check if our target database exists or can be accessed
    db = client.Maure-STC
    collections = db.list_collection_names()
    print(f"Collections in Maure-STC: {collections}")
    
except Exception as e:
    print(f"ERROR with certificate validation: {e}")
    
    try:
        # Try with relaxed TLS settings
        print("\nTrying with relaxed TLS settings...")
        client = MongoClient(uri, 
                           tlsAllowInvalidCertificates=True,
                           tlsAllowInvalidHostnames=True)
        client.admin.command('ping')
        print("SUCCESS: Connected to MongoDB Atlas with relaxed TLS settings!")
        
        # List databases to verify access
        dbs = client.list_database_names()
        print(f"Available databases: {dbs}")
        
        # Check if our target database exists or can be accessed
        db = client.Maure-STC
        collections = db.list_collection_names()
        print(f"Collections in Maure-STC: {collections}")
        
    except Exception as e2:
        print(f"ERROR with relaxed TLS settings: {e2}")