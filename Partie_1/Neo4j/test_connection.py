from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError
import psycopg2
from psycopg2 import OperationalError

# --- Configuration Neo4j ---
NEO4J_URI = "bolt://neo4j:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "spark123"

# --- Configuration PostgreSQL ---
POSTGRES_CONFIG = {
    "dbname": "projet_final",
    "user": "spark",
    "password": "spark123",
    "host": "projet_final_postgres",
    "port": 5432
}

# --- Test de connexion Neo4j ---
print("\n Test de connexion à Neo4j...")
try:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        result = session.run("RETURN 1 AS test")
        print("✅ Connexion à Neo4j réussie ! Résultat :", result.single()["test"])
except ServiceUnavailable as e:
    print("❌ Impossible de se connecter à Neo4j :", e)
except AuthError:
    print("❌ Échec de l'authentification Neo4j : identifiants incorrects")
except Exception as e:
    print("❌ Erreur inconnue Neo4j :", e)
finally:
    try:
        driver.close()
    except:
        pass

# --- Test de connexion PostgreSQL ---
print("\n Test de connexion à PostgreSQL...")
try:
    pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
    pg_cursor = pg_conn.cursor()
    pg_cursor.execute("SELECT 1;")
    print("✅ Connexion à PostgreSQL réussie ! Résultat :", pg_cursor.fetchone()[0])
    pg_cursor.close()
    pg_conn.close()
except OperationalError as e:
    print("❌ Impossible de se connecter à PostgreSQL :", e)
except Exception as e:
    print("❌ Erreur inconnue PostgreSQL :", e)
