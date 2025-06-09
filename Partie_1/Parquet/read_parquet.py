from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg
from io import StringIO
import sys
from datetime import datetime

spark = SparkSession.builder \
    .appName("ReadParquetExample") \
    .getOrCreate()

df = spark.read.parquet("/app/Parquet/sample_output_parquet")

log_path = "/app/logs/statistiques_parquet.txt"

# Rediriger la sortie vers un buffer pour log + console
buffer = StringIO()
original_stdout = sys.stdout
sys.stdout = buffer

# 📊 Affichage des données
print("\n Exemple de données chargées depuis les fichiers Parquet :\n")
df.show(10, truncate=False)

print("\nStatistiques sur les données :")

# Statistiques principales
total = df.count()
print(f"- Nombre total de documents : {total}")

communes_uniques = df.select("commune").distinct().count()
print(f"- Nombre de communes différentes : {communes_uniques}")

valeur_moyenne = df.select(avg("valeur_fonciere")).first()[0]
print(f"- Moyenne de la valeur foncière : {valeur_moyenne:.2f} €")

print("\n Top 5 des communes avec le plus de ventes :")
top_communes = df.groupBy("commune") \
    .count() \
    .orderBy(col("count").desc()) \
    .limit(5)
top_communes.show(truncate=False)

# Écriture dans le fichier
sys.stdout = original_stdout
with open(log_path, "w", encoding="utf-8") as f:
    f.write("=" * 60 + "\n")
    f.write(f"Rapport généré le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(buffer.getvalue())

# ✅ Impression dans la console pour vérif
print(buffer.getvalue())

spark.stop()
