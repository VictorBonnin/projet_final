from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, year, month, to_date, current_date, sha2, concat_ws
from datetime import datetime

# Création session Spark avec mémoire accrue
spark = SparkSession.builder \
    .appName("SilverLayerWriter") \
    .config("spark.mongodb.read.connection.uri", "mongodb://mongodb:27017/projet_final.streaming_resultats") \
    .config("spark.jars.packages",
            "org.mongodb.spark:mongo-spark-connector_2.12:3.0.1,"
            "org.postgresql:postgresql:42.2.27") \
    .config("spark.driver.memory", "4g") \
    .config("spark.executor.memory", "4g") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# Liste des années et mois à traiter
annees = range(2021, 2024)
mois = range(1, 13)

# Colonnes clés
colonnes_dedup = ["date_mutation", "code_postal", "valeur_fonciere", "commune", "type_local"]

for annee in annees:
    for m in mois:
        date_min = f"{annee}-{m:02d}-01"
        date_max = f"{annee}-{m + 1:02d}-01" if m < 12 else f"{annee + 1}-01-01"

        print(f"📦 Traitement {annee}-{m:02d}...")

        try:
            df_batch = spark.read \
                .format("mongo") \
                .option("uri", "mongodb://mongodb:27017") \
                .option("database", "projet_final") \
                .option("collection", "streaming_resultats") \
                .option("pipeline", f"""[
                    {{ "$match": {{
                        "date_mutation": {{
                            "$gte": {{ "$date": "{date_min}T00:00:00Z" }},
                            "$lt": {{ "$date": "{date_max}T00:00:00Z" }}
                        }}
                    }} }}
                ]""") \
                .load()

            if df_batch.rdd.isEmpty():
                print(f"⚠️ Aucun résultat pour {annee}-{m:02d}")
                continue

            # Nettoyage
            df_clean = df_batch \
                .withColumn("date_mutation", to_date("date_mutation")) \
                .withColumn("valeur_fonciere", col("valeur_fonciere").cast("float")) \
                .withColumn("surface_reelle_bati", col("surface_reelle_bati").cast("float")) \
                .withColumn("nombre_pieces_principales", col("nombre_pieces_principales").cast("int")) \
                .withColumn("valeur_fonciere", when(col("valeur_fonciere").isNull(), 0.0).otherwise(col("valeur_fonciere"))) \
                .withColumn("surface_reelle_bati", when(col("surface_reelle_bati").isNull(), 0.0).otherwise(col("surface_reelle_bati"))) \
                .withColumn("nombre_pieces_principales", when(col("nombre_pieces_principales").isNull(), 0).otherwise(col("nombre_pieces_principales"))) \
                .withColumn("part_date", current_date()) \
                .drop("_id") \
                .dropDuplicates(colonnes_dedup) \
                .withColumn("id_unique", sha2(concat_ws("||", *colonnes_dedup), 256)) \
                .repartition(5)

            # Écriture vers PostgreSQL
            df_clean.write \
                .format("jdbc") \
                .option("url", "jdbc:postgresql://postgres:5432/projet_final") \
                .option("dbtable", "silver_resultats") \
                .option("user", "spark") \
                .option("password", "spark123") \
                .option("driver", "org.postgresql.Driver") \
                .option("batchsize", 10000) \
                .mode("append") \
                .save()

            print(f"✅ Données {annee}-{m:02d} insérées.")

        except Exception as e:
            print(f"❌ Erreur pour {annee}-{m:02d} : {e}")

print("✅ Transfert complet terminé.")