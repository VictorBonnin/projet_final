from pymongo import MongoClient

try:
    client = MongoClient("mongodb://mongodb:27017", serverSelectionTimeoutMS=3000)
    client.server_info()  # Force la connexion
    print("✅ Connexion à MongoDB OK")
except Exception as e:
    print(f"❌ Connexion échouée : {e}")
