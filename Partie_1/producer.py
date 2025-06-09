from kafka import KafkaProducer
import json
import time
import csv
import os

# Configuration du producer Kafka
producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

fichiers_dir = '/app/donnees_brutes/fichiers_bruts/'
fichiers_txt = [f for f in os.listdir(fichiers_dir) if f.endswith('.txt')]

# Affichage des fichiers disponibles
print("📁 Fichiers disponibles :\n")
for i, f in enumerate(fichiers_txt):
    print(f"{i+1}. {f}")
print("\nEntrez les numéros des fichiers à traiter séparés par des virgules (ex: 1,3,4) ou '*' pour tous :")

choix = input("Votre sélection : ").strip()

if choix == "*":
    fichiers_choisis = fichiers_txt
else:
    try:
        indices = [int(i.strip()) - 1 for i in choix.split(",")]
        fichiers_choisis = [fichiers_txt[i] for i in indices if 0 <= i < len(fichiers_txt)]
    except Exception as e:
        print(f"❌ Erreur dans la sélection : {e}")
        exit(1)

# Topic Kafka
topic = 'donnees_topic'
batch_size = 20000
batch = []

for fichier in fichiers_choisis:
    fichier_source = fichier.replace('.txt', '')

    print("\n" + "=" * 80)
    print(f"📂 DÉBUT DU TRAITEMENT DU FICHIER : {fichier}")
    print("=" * 80 + "\n")

    total_lignes = 0

    with open(os.path.join(fichiers_dir, fichier), 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='|')
        for row in reader:
            message = {
                "date_mutation": row.get("Date mutation"),
                "nature_mutation": row.get("Nature mutation"),
                "valeur_fonciere": row.get("Valeur fonciere").replace(",", ".") if row.get("Valeur fonciere") else None,
                "code_postal": row.get("Code postal"),
                "commune": row.get("Commune"),
                "type_local": row.get("Type local"),
                "surface_reelle_bati": row.get("Surface reelle bati").replace(",", ".") if row.get("Surface reelle bati") else None,
                "nombre_pieces_principales": int(row.get("Nombre pieces principales")) if row.get("Nombre pieces principales") else None,
                "fichier_source": fichier_source
            }

            batch.append(message)
            total_lignes += 1

            if len(batch) == batch_size:
                for item in batch:
                    producer.send(topic, item)
                print(f"✅ {batch_size} messages envoyés.")
                batch = []
                time.sleep(1)

    if batch:
        for item in batch:
            producer.send(topic, item)
        print(f"✅ {len(batch)} messages restants envoyés.")
        batch = []

    print(f"\n✅ Fin de traitement du fichier : {fichier}")
    print(f"🧮 Total lignes envoyées : {total_lignes}\n")

producer.flush()
print("🏁 Tous les fichiers sélectionnés ont été traités avec succès.")