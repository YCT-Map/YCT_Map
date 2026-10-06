#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input
python manage.py assign_graph_display_labels --apply
python manage.py verify_current_map_baseline --apply

