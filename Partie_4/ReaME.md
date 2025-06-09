# Projet de Deep-Learning 

## 0. Données brutes

- Nos données sont issues du site datagouv.fr, site répertoriant d'immenses jeu de données. Nous avons voulu travailler sur le même jeu de données que notre projet de fin d'étude.
- Le but de notre projet de Deep-Learning va être d'analyser et de tester différents modèles pour pouvoir faire uen analyse prédictive sur l'année

- Voici les données que nosu allons utiliser :

Url global : https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres/

2024 - https://www.data.gouv.fr/fr/datasets/r/5ffa8553-0e8f-4622-add9-5c0b593ca1f8
2023 - https://www.data.gouv.fr/fr/datasets/r/bc213c7c-c4d4-4385-bf1f-719573d39e90
2022 - https://www.data.gouv.fr/fr/datasets/r/b4f43708-c5a8-4f30-80dc-7adfa1265d74
2021 - https://www.data.gouv.fr/fr/datasets/r/3942b268-04e7-4202-b96d-93b9ef6254d6
2020 - https://www.data.gouv.fr/fr/datasets/r/0d16005c-f68e-487c-811b-0deddba0c3f1

## 1. Architecture Générale

Le projet s’appuie sur une architecture distribuée de traitement de données, organisée autour des composants suivants :

- **Producer** : Lit les fichiers texte, structure les données en JSON et les envoie dans un topic Kafka (micro-batchs).
- **Kafka** : Sert d’intermédiaire de transport des messages, découple ingestion et traitement, assure résilience et scalabilité.
- **Spark Structured Streaming** : Consomme les messages Kafka, traite les données (parse JSON, corrige types, gère les valeurs nulles…), prépare les données pour le stockage.
- **MongoDB** : Stocke les données transformées (semi-structurées) dans une base dédiée (`projet_final`, collection `streaming_resultats`).
- **PostgreSQL** : Stocke les données qui vont être traitées pendant le deuxième streaming entre MongoDB et PostgreSQL. Cela va nous permettre d'éliminer les doublons ou lignes vides.

## 2. Passage et stockage dans PostgreSQL

Après transformation et nettoyage, les données sont injectées dans **PostgreSQL** afin de bénéficier d’un stockage structuré, optimisé pour l’analyse.

### A. Structuration et nettoyage

- Nettoyage des données brutes (suppression des doublons, correction des types, gestion des valeurs nulles).
- Passage d’un format semi-structuré (JSON/MongoDB) à un format tabulaire (`silver_resultats`).
- Ainsi, nous avons des données qui sont enregistrées et propres dans notre base de données PostgreSQL.

### B. Utilisation des données

- Notre projet tourne à l'aide de docker, qui va permettre a chaque service de tourner indépendament. Ainsi, nos données vont être stockées à 2 endroits distincts, deux volumes docker : 
    - Un volume qui contiendra les données de MongoDB
    - Un autre volume qui va contenir cette fois les données de PostgreSQL.

- De cette manière, nous pouvons récupérer les données facilement :
    - En se connectant directement au port local dédié à notre BDD.
    - En utilisant le volume docker contenant les données.

### C. Explications de cette méthode

- Nous avons voulu appliquer cette méthode car nous savons que notre jeu de données est immense, et qu'il n'était pas propre. Poure nous éviter des manipulations interminables dans notre environement prédictionnel, nous avons souhaité trouver une solution péraine qui regrouperait l'ensemble des données, mais de manière plus propre.

## 3. Comment lancer le projet sans lancer tout le traitement de données

- Il faudra tout d'abord se rendre dans un terminal, aller dans le dossier qui contient le docker compose, à savoir "projet_final/Partie_1/ " et lancer la commande "docker-compose up --build -d".
- Le projet démarera ainsi tranquillement. Ensuite, il faudra se rendre dans les volumes de docker, et supprimer le volume "partie_1_pgdata" pour le remplacer par celui qui est disponible en tarball à cette adresse : "https://www.transfernow.net/dl/20250608gjzZ8vYC".
- Le fichier sera ensuite à insérer via docker en veillant bien à le renommer correctement.

## 4. Passage au traitement des données en deep_learning.
--> fichier deep_learning_prediction.ipynb