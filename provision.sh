#!/usr/bin/env bash

echo "Installing Apache2 and setting up apache2 server..Please wait"

apt-get update > /dev/null 2>&1

apt-get install -y apache2 > /dev/null 2>&1

rm -rf /var/www

ln -fs /vagrant /var/www