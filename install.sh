#!/bin/bash

apt-get -y install python3-rpi.gpio
pip3 install coloredlog
pip3 install flask
pip3 install apscheduler
pip3 install json

cp ./parkpowGateOpener.py /etc/
cp ./parkpowServer.service /etc/systemd/system
systemctl enable parkpowServer.service
systemctl restart parkpowServer.service
systemctl status parkpowServer.service
