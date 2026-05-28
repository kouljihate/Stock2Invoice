import socket
import sys

# Test if we can reach the MongoDB Atlas servers on port 27017
hosts = [
    'ac-uoreu45-shard-00-00.vhxrozb.mongodb.net',
    'ac-uoreu45-shard-00-01.vhxrozb.mongodb.net', 
    'ac-uoreu45-shard-00-02.vhxrozb.mongodb.net'
]

print("Testing TCP connectivity to MongoDB Atlas hosts on port 27017:")
for host in hosts:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, 27017))
        if result == 0:
            print(f"[OK] {host}:27017 - Port is open")
        else:
            print(f"[FAIL] {host}:27017 - Port is closed or unreachable (error: {result})")
        sock.close()
    except Exception as e:
        print(f"[ERROR] {host}:27017 - Error: {e}")

print("\nTesting hostname resolution:")
for host in hosts:
    try:
        ip = socket.gethostbyname(host)
        print(f"[OK] {host} resolves to {ip}")
    except Exception as e:
        print(f"[FAIL] {host} failed to resolve: {e}")