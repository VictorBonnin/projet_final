import unittest
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

class TestSparkPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.spark = SparkSession.builder \
            .master("local[1]") \
            .appName("TestPipeline") \
            .getOrCreate()

    def test_cleaning_pipeline(self):
        # Données fictives
        data = [
            ("source1", "2023-01-01", "Vente", None, "75001", "Paris", "Appartement", None, None),
            ("source2", "2023-01-02", "Echange", "300000", "69000", "Lyon", "Maison", "100", "5")
        ]
        columns = [
            "fichier_source", "date_mutation", "nature_mutation", "valeur_fonciere",
            "code_postal", "commune", "type_local", "surface_reelle_bati", "nombre_pieces_principales"
        ]

        df = self.spark.createDataFrame(data, columns)

        # Application du nettoyage comme dans le script réel
        df = df.withColumn("valeur_fonciere", col("valeur_fonciere").cast("float")) \
               .withColumn("surface_reelle_bati", col("surface_reelle_bati").cast("float")) \
               .withColumn("nombre_pieces_principales", col("nombre_pieces_principales").cast("int"))

        df = df.fillna({
            "valeur_fonciere": 0.0,
            "surface_reelle_bati": 0.0,
            "nombre_pieces_principales": 0
        })

        # Vérification
        result = df.collect()
        self.assertEqual(result[0]["valeur_fonciere"], 0.0)
        self.assertEqual(result[0]["surface_reelle_bati"], 0.0)
        self.assertEqual(result[0]["nombre_pieces_principales"], 0)

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()

if __name__ == '__main__':
    unittest.main()