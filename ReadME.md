# Projet de Fin d'Études

## Structure du projet
```bash
PROJET_FINAL/
├── .github/                                # Config GitHub (CI/CD, workflows)
├── Consignes/                              # Consignes de travail
├── donnees_brutes/
│   ├── link_data.txt                       # Lien de téléchargement des données
│   └── fichiers_tests/
│       └── sample_data_2024.txt            # Données brutes pour tests
├── Partie_1/
│   ├── API_Postgre/                        # API REST sécurisée (FastAPI + PostgreSQL)
│   │   ├── app/
│   │   │   ├── routes/                     # Fichiers de routage (endpoints REST)
│   │   │   ├── auth.py                     # Authentification (JWT, hashing)
│   │   │   ├── database.py                 # Connexion PostgreSQL
│   │   │   ├── main.py                     # Point d’entrée FastAPI
│   │   │   ├── models.py                   # Modèles SQLAlchemy
│   │   │   ├── schemas.py                  # Schémas de validation (Pydantic)
│   │   │   └── security.py                 # Sécurité et tokens JWT
│   │   ├── .env                            # Variables d'environnement
│   │   ├── Dockerfile                      # Image Docker pour l'API
│   │   └── requirements.txt                # Dépendances Python API
│   ├── logs/
│   │   ├── log_pipeline_spark_stream.txt   # Logs du pipeline Spark Streaming
│   │   ├── logs_api.txt                    # Logs d'activité API
│   │   ├── statistiques_parquet.txt        # Statistiques d’exports Parquet
│   │   └── statistiques_redis.txt          # Statistiques sur Redis
│   ├── Neo4j/
│   │   ├── neo4j_transactions.py           # Écriture dans Neo4j
│   │   └── test_connection.py              # Test de connexion à Neo4j
│   ├── Parquet/
│   │   ├── output_parquet/                 # Exports complets
│   │   ├── sample_output_parquet/          # Échantillons d’export
│   │   ├── mongo_to_parquet.py             # Transformation Mongo → Parquet
│   │   └── read_parquet.py                 # Lecture de fichiers Parquet
│   ├── Silver_layer/
│   │   ├── spark_postgres_reader.py        # Lecture des données PostgreSQL
│   │   ├── spark_silver_writer.py          # Insertion Mongo → PostgreSQL
│   │   ├── test_connexion.py               # Tests de connectivité PostgreSQL
│   │   └── transformation_en_date.py       # Traitement des dates
│   ├── tests/
│   │   └── test_spark_pipeline.py          # Test global du pipeline Spark
│   ├── docker-compose.yml                  # Orchestration Spark, Mongo, Kafka, etc.
│   ├── dockerfile                          # Image Spark avec connecteurs Kafka/Mongo
│   ├── producer.py                         # Producer Kafka : envoi des données
│   ├── redis_example.py                    # Exemple de script Redis
│   ├── requirements.txt                    # Dépendances Python du pipeline
│   └── spark_stream_processor.py           # Traitement Spark Streaming → MongoDB
├── Partie_1_Streamlit_dashboard/
│   ├── app.py                              # Dashboard Streamlit (Bronze layer)
│   ├── dockerfile                          # Image Docker pour Streamlit
│   └── requirements.txt                    # Dépendances pour l’app web

├── reset_complet.sh                        # Réinitialisation complète du projet
├── reset_sans_postgre.sh                   # Réinitialisation sans le volume PostgreSQL
├── total_lignes.txt                        # Statistiques sur le volume total de lignes
├── ReadME.md                               # Présentation du projet
├── Soutenance.docx                         # Document de soutenance
```

## Nettoyage complet de l'environnement Docker

Avant de lancer proprement l’infrastructure, on va d'abord nettoyer notre environement pour repartir de zéro :  
Dans le dossier Projet_final :  
Il faut penser a mettre le fichier en "LF" et non pas en "CRLF".
```bash
bash reset_projet.sh
```

Lancer l'infrastructure :  
Dans le dossier Partie_1/, lancez les services avec Docker :
```bash
docker-compose up --build -d
```

Services inclus :  
kafka  
zookeeper  
mongodb  
spark (master + worker)  
spark-runner (conteneur pour exécuter les scripts Python)  
streamlit (visualisation simple des données de Mongo)  

Ajout du volume postgre si necessaire : 
```bash
docker run --rm -v partie_1_pgdata:/data -v "C:\Users\bonni\Documents\Ecole\Efrei\projet_final\backups:/backup" alpine tar -xzf /backup/partie_1_pgdata_backup.tar.gz -C /data

docker run --rm -v partie_1_pgdata:/data alpine rm -f /data/postmaster.pid
```

## Lancer les scripts de traitement
1. Lancer le consumer Spark Streaming  
Dans un terminal :
```bash
docker exec -it spark-runner bash
cd /app
python spark_stream_processor.py
```
Ce script lit les données du topic Kafka, les parse selon un schéma JSON et les insère dans MongoDB (projet_final.streaming_resultats).

2. Lancer le producer Kafka
Dans un deuxième terminal :  
```bash
docker exec -it spark-runner bash
cd /app
python producer.py
```
Ce script lit les fichiers .txt de données foncières (séparateur |), nettoie les colonnes, et envoie les données dans le topic Kafka donnees_topic.

3. Vérifier les données dans MongoDB
```bash
docker exec -it partie_1-mongodb mongosh
```

Puis dans le shell Mongo :
```js
use projet_final
db.streaming_resultats.find().pretty()
```

4. Visualiser les données avec Streamlit  
Pour visualiser plus proprement les données, on peut aussi se rendre sur Streamlit, à l'adresse suivante :
```bash
http://localhost:8501/
```

## Traitement vers la Silver Layer (PostgreSQL)

5. Écriture des données nettoyées dans PostgreSQL (Silver)
```bash
docker exec -it spark-runner bash
cd Silver_layer/
python spark_silver_writer.py
```
Ce script :  
Lit les données de MongoDB,  
Les nettoie (types, valeurs nulles, parsing date),  
Ajoute la colonne date_ingestion,  
Écrit le tout dans PostgreSQL dans la table silver_resultats.  

6. Vérification des données Postgres (optionnel)
```bash
python spark_postgres_reader.py
```
Grace à cela, nous pouvons lire les données (dans le terminal) de PostgreSQL pour vérifier qu'elles ont bien été insérées.

7. Vérification des données dans DBeaver  
Nous pouvons maintenant aller constater que les données sont bien ingérées dans notre base PostgreSQL en allant directement dans un éditeur tel que DBeaver.  
Une fois l'application lancée, faire 'CRLT + MAJ + N'. Une page va s'ouvrir pour selectionner la connexion souhaitée : PostgreSQL.  
Maintenant, il nous plus que rentrer les informations suivantes :  
    - projet_final  
    - spark  
    - spark123  

8. Création d’un CUBE analytique (vue PostgreSQL)

Une fois les données nettoyées et insérées dans la table `silver_resultats`, nous pouvons créer une **vue agrégée** qui servira de base à l’analyse multidimensionnelle (cube analytique).  
Cela permet d’analyser les ventes par commune, type de bien et année, tout en conservant les indicateurs clés comme le nombre de ventes, la valeur foncière totale, ou la surface moyenne.

Lancer cette commande PostgreSQL dans DBeaver :

```sql
CREATE MATERIALIZED VIEW cube_ventes AS
SELECT 
  type_local,
  commune,
  EXTRACT(YEAR FROM date_mutation) AS annee,
  COUNT(*) AS nb_ventes,
  SUM(valeur_fonciere) AS total_valeur_fonciere,
  AVG(surface_reelle_bati) AS surface_moyenne
FROM silver_resultats
GROUP BY type_local, commune, EXTRACT(YEAR FROM date_mutation);
```

Nous pouvons ensuite regarder les résultats de cette vue en lancant cette requête :  
```sql
-- Total des ventes par commune en 2022
SELECT commune, SUM(total_valeur_fonciere)
FROM cube_ventes
WHERE annee = 2022
GROUP BY commune;
```

10. Modélisation de la base gold_layer

Création des tables :  

Table des communes, avec un Id qui sera connecté à notre table principale (transactions)  
```sql
-- Table des communes
CREATE TABLE IF NOT EXISTS communes (
    id_commune SERIAL PRIMARY KEY,
    nom_commune TEXT UNIQUE NOT NULL
);
```

Table des locaux (infrastructures), avec un Id qui sera connecté à notre table principale (transactions)  
```sql
-- Table des types de locaux
CREATE TABLE IF NOT EXISTS types_locaux (
    id_type SERIAL PRIMARY KEY,
    type_local TEXT UNIQUE NOT NULL
);
```

Table des types de transactions, avec un Id qui sera connecté à notre table principale (transactions)
```sql
-- Table des natures de mutation
CREATE TABLE IF NOT EXISTS natures_mutation (
    id_nature SERIAL PRIMARY KEY,
    nature_mutation TEXT UNIQUE NOT NULL
);
```

Table des transactions, qui sera notre table principale.
```sql
-- Table des transactions (Gold Layer principale)
CREATE TABLE IF NOT EXISTS transactions (
    id_transaction UUID PRIMARY KEY,
    id_unique VARCHAR(255),
    code_postal VARCHAR(10),
    date_mutation DATE,
    fichier_source TEXT,
    part_date DATE,
    valeur_fonciere FLOAT,
    surface_reelle_bati FLOAT,
    nombre_pieces_principales INT,
    id_commune INT REFERENCES communes(id_commune),
    id_type INT REFERENCES types_locaux(id_type),
    id_nature INT REFERENCES natures_mutation(id_nature)
);
```

Injection des données :  
Maintenant que nos tables ont bien été créées, il faut y injecter les données. Nous pouvons, pour faire cela, utiliser les données de notre table ‘silver_layer’, car nous savons que les données ont déjà été nettoyées. Ainsi, grâce a ce travail, l’injection ne se résume plus qu’en quelques lignes.  

```sql
-- Insérer les communes
INSERT INTO communes (nom_commune)
SELECT DISTINCT commune
FROM silver_resultats
WHERE commune IS NOT NULL;

-- Insérer les types de locaux
INSERT INTO types_locaux (type_local)
SELECT DISTINCT type_local
FROM silver_resultats
WHERE type_local IS NOT NULL;

-- Insérer les natures de mutation
INSERT INTO natures_mutation (nature_mutation)
SELECT DISTINCT nature_mutation
FROM silver_resultats
WHERE nature_mutation IS NOT NULL;

-- Insérer les données globales de la table principale
INSERT INTO transactions (
    id_transaction,
    id_unique,
    code_postal,
    date_mutation,
    fichier_source,
    part_date,
    valeur_fonciere,
    surface_reelle_bati,
    nombre_pieces_principales,
    id_commune,
    id_type,
    id_nature
)
SELECT
  gen_random_uuid() AS id_transaction,
  sr.id_unique,
  sr.code_postal,
  sr.date_mutation,
  sr.fichier_source,
  sr.part_date,
  sr.valeur_fonciere,
  sr.surface_reelle_bati,
  sr.nombre_pieces_principales,
  c.id_commune,
  t.id_type,
  n.id_nature
FROM silver_resultats sr
JOIN communes c ON sr.commune = c.nom_commune
JOIN types_locaux t ON sr.type_local = t.type_local
JOIN natures_mutation n ON sr.nature_mutation = n.nature_mutation;
```

Pour finaliser la Gold_layer, nous allons maintenant créer des vues exploitant les tables que nous venons de créer.

Vue principale :  
```sql
CREATE OR REPLACE VIEW dl_gold_transactions_detaillees AS
SELECT 
    t.id_transaction,
    t.code_postal,
    c.nom_commune,
    t.date_mutation,
    t.fichier_source,
    t.part_date,
    t.valeur_fonciere,
    t.surface_reelle_bati,
    t.nombre_pieces_principales,
    tl.type_local,
    nm.nature_mutation
FROM transactions t
JOIN communes c ON t.id_commune = c.id_commune
JOIN types_locaux tl ON t.id_type = tl.id_type
JOIN natures_mutation nm ON t.id_nature = nm.id_nature;
```

Vue des statistiques par commune :  
```sql
CREATE OR REPLACE VIEW dl_gold_stats_par_commune AS
SELECT 
    c.nom_commune,
    COUNT(*) AS nb_transactions,
    ROUND(AVG(t.valeur_fonciere)) AS valeur_moyenne,
    ROUND(SUM(t.surface_reelle_bati)) AS surface_totale
FROM transactions t
JOIN communes c ON t.id_commune = c.id_commune
GROUP BY c.nom_commune
ORDER BY nb_transactions DESC;
```

Vue des tendances par type de bien :  
```sql
CREATE OR REPLACE VIEW dl_gold_stats_par_type_local AS
SELECT 
    tl.type_local,
    COUNT(*) AS nb_ventes,
    ROUND(AVG(t.valeur_fonciere)) AS prix_moyen
FROM transactions t
JOIN types_locaux tl ON t.id_type = tl.id_type
GROUP BY tl.type_local
ORDER BY prix_moyen DESC;
```

Exemple de scprit pour vérifier les données :
```sql
SELECT * FROM dl_gold_transactions_detaillees;
```

11. Utilisation de Neo4j - Base orientée Graphs 

Aller dans le container Spark-runner, puis vérifier que la connection s'effectue bien :
```bash
docker exec -it spark-runner bash
cd /app/Neo4j
python test_connection.py
```

Ensuite, une fois que la conenction est ok, on peut lancer le script principal pour envoyer les données vers Neo4j :
```bash
docker exec -it spark-runner bash
cd /app/Neo4j
python neo4j_transactions.py
```

Maintenant, on peut aller voir si les données ont bien été envoyées :
```bash
http://localhost:7474
```

Pour se connecter, il faut simplement rentrer le user : *Neo4j* et le mot de passe : *spark123*.
Nous pouvons maintenant acceder à l'interface de Neo4j tout en étant connecté à notre base Mongo.

La structure a laquelle nous avons pensé est la suivante :  
```ruby
(:NatureMutation)
   └─[:A_POUR_TYPE]→ (:TypeLocal)
        └─[:A_POUR_LIEU]→ (:Commune)
             └─[:A_ENREGISTRE]→ (:Mutation {date, valeur, id})
```

Pour retirer la data déjà présente dans Neo4j :
```ruby
MATCH (n) DETACH DELETE n;
```

Pour afficher les données :
```ruby
MATCH (n) RETURN n LIMIT 100;
```

Pour afficher un exemple de noeuds avec un type de local précis :
```ruby
MATCH (n:NatureMutation)-[:A_POUR_TYPE]->(t:TypeLocal {nom: "Maison"})
      -[:A_POUR_LIEU]->(c:Commune)-[:A_ENREGISTRE]->(m:Mutation)
RETURN n, t, c, m
LIMIT 100
```

Afficher les communes par nombre de ventes : 
```ruby
MATCH (c:Commune)-[:A_ENREGISTRE]->(m:Mutation)
RETURN c.nom AS Commune, count(m) AS NombreMutations
ORDER BY NombreMutations DESC
LIMIT 100
```

Afficher les transactions d'une ville en particulier : 
```ruby
MATCH (c:Commune {nom: "FOISSIAT"})-[:A_ENREGISTRE]->(m:Mutation)
RETURN m.date AS Date, m.valeur AS Valeur
ORDER BY m.date
LIMIT 100
```

Pour avoir les résultats avec un affichage visuel :
```ruby
MATCH (n:NatureMutation {nom: "Vente"})-[:A_POUR_TYPE]->(t:TypeLocal)
MATCH (t)-[:A_POUR_LIEU]->(c:Commune {nom: "FOISSIAT"})
MATCH (c)-[:A_ENREGISTRE]->(m:Mutation)
WHERE t.nom <> "Inconnu"
RETURN n, t, c, m
LIMIT 100
```

12. Utilisation de Parquet - Base oritentée colonne
Dans un terminal :
```bash
docker exec -it spark-runner bash
cd /Parquet
python mongo_to_parquet.py

python read_parquet.py
```

13. Utilisation de Redis - Base clé valeurs
Dans un terminal :
```bash
docker exec -it spark-runner bash
cd /app
python redis_example.py
```

14. Utilisation de l'API Postgre :

Se rendre sur :
```bash
http://localhost:8000/docs#/
```

Aller dans 'Post utilisateurs', faire 'Try it out', et mettre ses identifiants pou créer son compte, par exemple :
```json
{
  "nom": "Victor",
  "email": "victor@email.com",
  "mot_de_passe": "victor"
}
```

Cliquer ensuite sur 'Execute'. Vérifier juste en dessous que la requête à bien retournée un code 200, ce qui indique que tout s'est bien passé.

Maintenant que notre utilisateur est créé, un peut vérifier dans notre base PostgreSQL que c'est bien le cas. Pour cela, nous avons juste a faire cette simple requête :
```sql
select * from utilisateurs u 
```

Vous verrez normalement votre utilisateur créé.

Maintenant, il faut se connecter pour récupérer notre token, qui sera notre clé pour pouvoir faire des requêtes sur les données globales.

Ainsi, il faut aller dans 'Post login', faire 'Try it out', et rentrer les informations suivantes :

```
grant_type : password
username : mettre votre email (victor@email.com)
password : mettre votre mot_de_passe (victor)
scope : laisser/mettre vide
client_id : laisser/mettre vide
client_secret : laisser/mettre vide
```

Dans le retour de la requête, on peut voir notre token. Il faut le récupérer, cela va nous permettre de se connecter à l'API pour faire les requêtes sécurisées. 

Une fois que vous avez copié votre token, il faut aller tout en haut de la page, et cliquer sur 'Authorize'. Il faut ensuite y rentrer votre token. CLiquez ensuite sur 'Close'.

Maintenant qu'on est connectés, on peut envoyer des requêtes vers nos données. Pour se faire, il faut aller dans 'Get resultats', et cliquer sur 'Try it out'. Ensuite, on peut rentrer les élements que l'ont veut.
A savoir, chaque token expire au bout de 30 minutes.

Une fois le token validé, on peut rentre un code postal et une ville et avoir un retour sur les transactions trouvées. Par exemple :
```
code_postal : 73490
commune : LA RAVOIRE
```