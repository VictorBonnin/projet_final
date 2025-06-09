from datetime import datetime
import pytz
from pymongo import MongoClient
import redis

# Connexion à MongoDB
mongo_client = MongoClient("mongodb://mongodb:27017/")
db = mongo_client["projet_final"]
collection = db["streaming_resultats"]

# Connexion à Redis
r = redis.Redis(host='redis', port=6379)

# Calcul des statistiques
total_docs = collection.count_documents({})
avg_valeur = collection.aggregate([
    {"$group": {"_id": None, "moyenne": {"$avg": "$valeur_fonciere"}}}
])
avg_result = next(avg_valeur, {"moyenne": 0})

# Enregistrement dans Redis
r.set("stat_total_documents", total_docs)
r.set("stat_moyenne_valeur_fonciere", round(avg_result["moyenne"], 2))

# Top 5 des communes avec le plus de transactions
top_communes = collection.aggregate([
    {"$group": {"_id": "$commune", "nb": {"$sum": 1}}},
    {"$sort": {"nb": -1}},
    {"$limit": 5}
])
r.delete("top_communes")
for commune in top_communes:
    r.rpush("top_communes", f"{commune['_id']} ({commune['nb']})")

# 🔁 Conversion vers UTC+2
paris_tz = pytz.timezone('Europe/Paris')
formatted_date = datetime.now(paris_tz).strftime("%Y-%m-%d %H:%M:%S")
r.set("last_update_stats", formatted_date)

# Affichage console
print("\n Statistiques enregistrées dans Redis :")
print(f" - Total documents : {total_docs}")
print(f" - Moyenne valeur foncière : {round(avg_result['moyenne'], 2)}")
print(" - Top 5 communes :")
top_5 = r.lrange("top_communes", 0, -1)
for commune in top_5:
    print("   ·", commune.decode())

print(f" - Dernière mise à jour : {r.get('last_update_stats').decode()}")

# Sauvegarde en fichier texte
avg_valeur_fonciere = round(avg_result["moyenne"], 2)

with open("logs/statistiques_redis.txt", "a", encoding="utf-8") as f:
    f.write("Statistiques enregistrées dans Redis :\n")
    f.write(f"- Total documents : {total_docs}\n")
    f.write(f"- Moyenne valeur foncière : {avg_valeur_fonciere:.2f}\n")
    f.write("- Top 5 communes :\n")
    for commune in top_5:
        commune, count = commune.decode().rsplit(" (", 1)
        count = count.rstrip(")")
        f.write(f"  - {commune} ({count})\n")
    f.write(f"- Dernière mise à jour : {formatted_date}\n")
    f.write("-" * 40 + "\n")