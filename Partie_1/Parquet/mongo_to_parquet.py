from pyspark.sql import SparkSession
import time

# Création de la session Spark
spark = SparkSession.builder \
    .appName("MongoToParquetSample") \
    .config("spark.mongodb.read.connection.uri", "mongodb://mongodb:27017/projet_final.streaming_resultats") \
    .config("spark.driver.memory", "2g") \
    .config("spark.executor.memory", "2g") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

start = time.time()
print("🚀 Lecture de l'échantillon depuis MongoDB...")

# Lecture brute (non partitionnée, volontaire ici car sample)
df = spark.read \
    .format("com.mongodb.spark.sql.DefaultSource") \
    .option("uri", "mongodb://mongodb:27017") \
    .option("database", "projet_final") \
    .option("collection", "streaming_resultats") \
    .load()

# Création d'un échantillon aléatoire de 20 000 lignes
sample_df = df.sample(withReplacement=False, fraction=0.1, seed=42).limit(20000)

# Aperçu
print("\n📊 Aperçu de l'échantillon :")
sample_df.show(5)
print(f"\n📌 Taille de l'échantillon : {sample_df.count()}")
sample_df.printSchema()

# Écriture Parquet
output_path = "/app/Parquet/sample_output_parquet"
sample_df.write.mode("overwrite").option("compression", "snappy").parquet(output_path)

print(f"\n✅ Échantillon exporté avec succès au format Parquet dans : {output_path}")
print(f"⏱️ Temps total : {time.time() - start:.2f} secondes")

spark.stop()