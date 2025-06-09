#!/bin/bash

echo " "
echo "🛑 Arrêt et suppression des conteneurs du projet..."
cd "$(dirname "$0")"
docker-compose down
docker-compose -f ./Partie_1/docker-compose.yml down --remove-orphans

echo " "
echo "🧹 Suppression du volume MongoDB (réinitialisation base Mongo)"
docker volume rm partie_1_mongo_data partie_1_neo4j_data || echo "⚠️ Volume Mongo déjà supprimé ou introuvable."

echo "🧹 Suppression des volumes orphelins..."
docker volume prune -f

echo " "
echo "🧽 Nettoyage des images inutilisées..."
docker image prune -f

echo " "
echo "✅ Projet réinitialisé (PostgreSQL intact)."
