from pymongo import MongoClient
import certifi

uri = "mongodb+srv://koul:%3C%40LooK9LooK%3E@cluster0.vhxrozb.mongodb.net/Maure-STC?appName=Cluster0"

try:
    client = MongoClient(uri, 
                         tlsAllowInvalidCertificates=True,
                         tlsAllowInvalidHostnames=True)
    # Ping the server to confirm connection
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(f"Error: {e}")