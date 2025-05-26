#! /bin/sh

set -e

alembic upgrade head
flask --app vision.servicenode.wsgi:application run --host=0.0.0.0 --port=8080