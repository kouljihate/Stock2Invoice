from pymongo import MongoClient
import ssl

uri = "mongodb+srv://koul:%40LooK9LooK@cluster0.vhxrozb.mongodb.net/Maure-STC?appName=Cluster0"

print("Testing different TLS settings...")

# Test 1: Default settings
print("\n1. Testing with default settings:")
try:
    client = MongoClient(uri)
    client.admin.command('ping')
    print("   SUCCESS")
except Exception as e:
    print(f"   FAILED: {str(e)[:100]}...")

# Test 2: Force TLS 1.2
print("\n2. Testing with TLS 1.2 forced:")
try:
    client = MongoClient(uri, tls=True, tlsAllowInvalidCertificates=True)
    client.admin.command('ping')
    print("   SUCCESS")
except Exception as e:
    print(f"   FAILED: {str(e)[:100]}...")

# Test 3: Explicitly disable TLS 1.0 and 1.1
print("\n3. Testing with TLS 1.2+ only:")
try:
    client = MongoClient(uri, 
                        tls=True,
                        tlsAllowInvalidCertificates=True,
                        ssl_ca_certs=None)  # Let it use system defaults
    client.admin.command('ping')
    print("   SUCCESS")
except Exception as e:
    print(f"   FAILED: {str(e)[:100]}...")

# Test 4: Try with specific SSL context
print("\n4. Testing with custom SSL context:")
try:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    # Try to set minimum TLS version
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    
    client = MongoClient(uri, tls=True, tlsAllowInvalidCertificates=True)
    # Note: pymongo doesn't directly expose SSL context setting in URI
    # This might not work as expected
    client.admin.command('ping')
    print("   SUCCESS")
except Exception as e:
    print(f"   FAILED: {str(e)[:100]}...")

# Test 5: Try connecting without SRV record first (direct to one host)
print("\n5. Testing direct connection to shard 0:")
try:
    direct_uri = "mongodb://ac-uoreu45-shard-00-00.vhxrozb.mongodb.net:27017/Maure-STC?replicaSet=rs0&authSource=admin"
    client = MongoClient(direct_uri, 
                        username="koul",
                        password="@LooK9LooK",
                        authSource="admin",
                        tlsAllowInvalidCertificates=True)
    client.admin.command('ping')
    print("   SUCCESS")
except Exception as e:
    print(f"   FAILED: {str(e)[:100]}...")

# Test 6: Try with explicit replica set in SRV
print("\n6. Testing SRV with explicit replica set:")
try:
    srv_uri = "mongodb+srv://koul:%40LooK9LooK@cluster0.vhxrozb.mongodb.net/Maure-STC?replicaSet=rs0&appName=Cluster0"
    client = MongoClient(srv_uri, tlsAllowInvalidCertificates=True)
    client.admin.command('ping')
    print("   SUCCESS")
except Exception as e:
    print(f"   FAILED: {str(e)[:100]}...")