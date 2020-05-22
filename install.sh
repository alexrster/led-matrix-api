#!/bin/sh

apt update
apt upgrade
apt install build-essential python-dev python-pip nginx uwsgi uwsgi-plugin-python
pip install virtualenv

mkdir -p /var/www/led-matrix-api
chown -R pi /var/www/led-matrix-api
cp -r ./* /var/www/led-matrix-api/
touch /tmp/led-matrix-api.sock
chown -R pi /tmp/led-matrix-api.sock

cp dist/nginx-site /etc/nginx/sites-available/led-matrix-api
ln -s /etc/nginx/sites-available/led-matrix-api /etc/nginx/sites-enabled/led-matrix-api
cp dist/uwsgi.ini /etc/uwsgi/apps-available/led-matrix-api.ini
ln -s /etc/uwsgi/apps-available/led-matrix-api.ini /etc/uwsgi/apps-enabled/led-matrix-api.ini

export _dir = $(pwd)
cd /var/www/led-matrix-api
virtualenv .env
source .env/bin/activate
pip install flask
deactivate

cd $_dir

systemctl restart nginx uwsgi
