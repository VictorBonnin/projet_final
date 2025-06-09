from pymongo import MongoClient
from datetime import datetime

# Connexion MongoDB
client = MongoClient("mongodb://mongodb:27017/")
db = client["projet_final"]
collection = db["streaming_resultats"]

# Compteur
modifies = 0
skipped = 0

for doc in collection.find({}, {"_id": 1, "date_mutation": 1}):
    date_value = doc.get("date_mutation")

    if isinstance(date_value, str):
        try:
            # Conversion depuis le format français JJ/MM/AAAA
            parsed_date = datetime.strptime(date_value, "%d/%m/%Y")
            collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"date_mutation": parsed_date}}
            )
            modifies += 1
        except Exception as e:
            print(f"❌ Erreur conversion : {date_value} (id={doc['_id']}) - {e}")
            skipped += 1
    else:
        skipped += 1

print(f"✅ Conversion terminée : {modifies} dates transformées, {skipped} ignorées.")