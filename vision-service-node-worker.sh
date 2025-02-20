#! /bin/sh

celery -A vision.servicenode worker -l INFO -n vision.servicenode -Q transfers,bids,transactions
