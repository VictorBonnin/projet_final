from pyspark.sql import SparkSession

# Création de la session Spark
spark = SparkSession.builder \
    .appName("PostgresReader") \
    .config("spark.jars.packages", "org.postgresql:postgresql:42.2.27") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# Lecture des données depuis PostgreSQL
df = spark.read \
    .format("jdbc") \
    .option("url", "jdbc:postgresql://postgres:5432/projet_final") \
    .option("dbtable", "silver_resultats") \
    .option("user", "spark") \
    .option("password", "spark123") \
    .option("driver", "org.postgresql.Driver") \
    .load()

# Affichage
print(f"✅ Nombre de lignes dans la table : {df.count()}")
df.printSchema()
df.show(20, truncate=False)