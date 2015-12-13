#!/bin/bash
echo "** podplayer installer **"
echo 'This will take a long time to run - time to grab a coffee (or even dinner).'
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi
echo "apt-get installs"
apt-get update
apt-get -y upgrade
apt-get -y install python-pip
apt-get -y install python-serial mpd mpc rpi.gpio	
echo 'pip installs...'
pip install beautifulsoup4
pip install requests
pip install python-mpd2
pip install logging
pip install feedparser
pip install urllib3
echo 'configure system files'
cp mpd.conf /etc
cp startradio /etc/init.d
chmod 755 /etc/init.d/startradio
# update-rc.d startradio defaults
cp sampleconfig.py config.py
chmod 666 config.py
echo 'Setting up runtime environment'
chmod +x radio.py
mkdir log
chown pi log
echo '*************************'
echo 'You still need to:'
echo '1. update the keys in the config.py file'

