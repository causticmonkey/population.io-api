#!/bin/sh

echo ''
echo 'UPDATING AND RUNNING SERVER'
echo '---------------------------'

# Shut down existing gunicorns
ps aux | grep -ie gunicorn | awk '{print $2}' | xargs kill

# Update project
cd ~/population.io
git pull

# Activate virtualenv
. venv/bin/activate

# Run gunicorn server forked
echo 'Launching server at http://localhost:9999/...'
gunicorn -b 0.0.0.0:8000 population_io.wsgi:application
