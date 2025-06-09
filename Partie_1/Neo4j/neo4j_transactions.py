import psycopg2
from neo4j import GraphDatabase
import time

# Configuration des connexions
POSTGRES_CONFIG = {
    "dbname": "projet_final",
    "user": "spark",
    "password": "spark123",
    "host": "projet_final_postgres",
    "port": 5432
}

NEO4J_URI = "bolt://neo4j:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "spark123"

# Connexion à PostgreSQL
pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
pg_cursor = pg_conn.cursor()

# Requête SQL
pg_cursor.execute("""
    SELECT commune, nature_mutation, type_local, date_mutation, valeur_fonciere
    FROM silver_resultats
""")
rows = pg_cursor.fetchall()
total_rows = len(rows)
print(f"🔍 Nombre total de lignes récupérées depuis PostgreSQL : {total_rows}")

# Connexion à Neo4j
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Création des index
index_queries = [
    "CREATE INDEX IF NOT EXISTS FOR (n:NatureMutation) ON (n.nom)",
    "CREATE INDEX IF NOT EXISTS FOR (t:TypeLocal) ON (t.nom)",
    "CREATE INDEX IF NOT EXISTS FOR (c:Commune) ON (c.nom)"
]
with driver.session() as session:
    for query in index_queries:
        session.run(query)
print("✅ Index créés (si nécessaires).")

# Fonction d'insertion par batch
def insert_batch(tx, batch):
    tx.run("""
        UNWIND $rows AS row
        MERGE (n:NatureMutation {nom: row.nature})
        MERGE (t:TypeLocal {nom: row.type_local})
        MERGE (c:Commune {nom: row.commune})

        MERGE (n)-[:A_POUR_TYPE]->(t)
        MERGE (t)-[:A_POUR_LIEU]->(c)

        CREATE (m:Mutation {
            date: row.date,
            valeur: row.valeur
        })

        MERGE (c)-[:A_ENREGISTRE]->(m)
    """, rows=batch)

# Insertion par batchs avec logs
batch_size = 2000  # Tu peux tester 1000 ou 2000 selon tes performances
with driver.session() as session:
    batch = []
    processed = 0
    start_time = time.time()

    for row in rows:
        commune, nature, type_local, date, valeur = row
        if commune and date and valeur:
            batch.append({
                "commune": commune,
                "nature": nature or "Inconnue",
                "type_local": type_local or "Inconnu",
                "date": str(date),
                "valeur": float(valeur or 0.0)
            })
            if len(batch) >= batch_size:
                session.execute_write(insert_batch, batch)
                processed += len(batch)
                elapsed = time.time() - start_time
                print(f"📦 {processed}/{total_rows} lignes insérées ({processed * 100 // total_rows}%) - Temps écoulé : {elapsed:.2f} s")
                batch = []

    # Dernier batch
    if batch:
        session.execute_write(insert_batch, batch)
        processed += len(batch)
        elapsed = time.time() - start_time
        print(f"📦 {processed}/{total_rows} lignes insérées (100%) - Temps total : {elapsed:.2f} s")

print("✅ Importation terminée avec succès.")

# Fermeture des connexions
driver.close()
pg_cursor.close()
pg_conn.close()