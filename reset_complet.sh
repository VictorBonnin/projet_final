#!/bin/bash

echo " "
echo "🛑 Arrêt et suppression de tous les conteneurs du projet..."
cd "$(dirname "$0")"
docker-compose down -v
docker-compose -f ./Partie_1/docker-compose.yml down -v --remove-orphans

echo " "
echo "🗑️ Suppression des volumes personnalisés..."
docker volume rm partie_1_mongo_data partie_1_pgdata partie_1_neo4j_data || echo "⚠️ Certains volumes n'existent peut-être pas."

echo "🧹 Suppression des volumes orphelins..."
docker volume prune -f

echo " "
echo "🧽 Nettoyage des images inutilisées..."
docker image prune -f

echo " "
echo "🧼 Suppression complète effectuée. Projet remis à zéro."