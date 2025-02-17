#!/bin/sh
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE ROLE "vision-service-node" WITH LOGIN PASSWORD 'vision';
    CREATE DATABASE "vision-service-node" WITH OWNER "vision-service-node";
    CREATE DATABASE "vision-service-node-celery" WITH OWNER "vision-service-node";
    CREATE DATABASE "vision-service-node-test" WITH OWNER "vision-service-node";
EOSQL
