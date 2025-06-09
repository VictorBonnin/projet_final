import time
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, when, to_date
from pyspark.sql.types import StructType, StringType

# 🚀 Création de la session Spark avec MongoDB
spark = SparkSession.builder \
    .appName("KafkaToMongoStreaming") \
    .config("spark.mongodb.write.connection.uri", "mongodb://mongodb:27017/") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# 🧱 Schéma JSON initial (tout en StringType)
schema = StructType() \
    .add("fichier_source", StringType()) \
    .add("date_mutation", StringType()) \
    .add("nature_mutation", StringType()) \
    .add("valeur_fonciere", StringType()) \
    .add("code_postal", StringType()) \
    .add("commune", StringType()) \
    .add("type_local", StringType()) \
    .add("surface_reelle_bati", StringType()) \
    .add("nombre_pieces_principales", StringType())

# 🔄 Lecture depuis Kafka
df_kafka = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "donnees_topic") \
    .option("startingOffsets", "latest") \
    .load()

# 📦 Parsing du JSON
df_parsed = df_kafka.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")) \
    .filter(col("data").isNotNull()) \
    .select("data.*")

# ✨ Caster correctement les types numériques après parsing
df_parsed = df_parsed \
    .withColumn("valeur_fonciere", col("valeur_fonciere").cast("float")) \
    .withColumn("surface_reelle_bati", col("surface_reelle_bati").cast("float")) \
    .withColumn("nombre_pieces_principales", col("nombre_pieces_principales").cast("int"))

# 🗓️ Convertir la date_mutation de string "dd/MM/yyyy" vers un DateType réel
df_parsed = df_parsed.withColumn("date_mutation", to_date("date_mutation", "dd/MM/yyyy"))

# 🔥 Remplacer uniquement les NULL par 0
df_parsed = df_parsed.withColumn(
    "valeur_fonciere",
    when(col("valeur_fonciere").isNull(), 0.0).otherwise(col("valeur_fonciere"))
).withColumn(
    "surface_reelle_bati",
    when(col("surface_reelle_bati").isNull(), 0.0).otherwise(col("surface_reelle_bati"))
).withColumn(
    "nombre_pieces_principales",
    when(col("nombre_pieces_principales").isNull(), 0).otherwise(col("nombre_pieces_principales"))
)

# 📝 Fonction d'écriture avec LOGS visibles pour chaque micro-batch
LOG_PATH = "/app/logs/log_pipeline_spark_stream.txt"

def write_to_mongo(batch_df, batch_id):
    start_time = time.time()
    line_count = batch_df.count()
    
    try:
        batch_df.write \
            .format("mongo") \
            .option("uri", "mongodb://mongodb:27017") \
            .option("database", "projet_final") \
            .option("collection", "streaming_resultats") \
            .mode("append") \
            .save()

        duration = round(time.time() - start_time, 2)
        log_line = f"[{datetime.now()}] ✅ Batch {batch_id} - {line_count} lignes - {duration}s\n"

    except Exception as e:
        log_line = f"[{datetime.now()}] ❌ Batch {batch_id} - ERREUR : {str(e)}\n"

    # Écriture dans un fichier log
    with open(LOG_PATH, "a") as f:
        f.write(log_line)

    print(log_line.strip())

# ▶️ Démarrage du stream avec checkpoint
query = df_parsed.writeStream \
    .foreachBatch(write_to_mongo) \
    .option("checkpointLocation", "/tmp/checkpoints/kafka_to_mongo") \
    .trigger(processingTime="5 seconds") \
    .start()

query.awaitTermination()
