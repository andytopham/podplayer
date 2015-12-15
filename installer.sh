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
# next one is needed for wiringpi2
apt-get -y install python-dev
echo 'pip installs...'
pip install beautifulsoup4
pip install requests
pip install python-mpd2
pip install logging
pip install feedparser
pip install urllib3
echo '** Installing pygame **'
apt-get -y install python-pygame
echo '** Installing wiringpi2 (needed for gaugette) **'
pip install wiringpi2
echo '** Installing gaugette **'
git clone git://github.com/guyc/py-gaugette.git
cd py-gaugette
python setup.py install
echo '** Installing Adafruit stuff **'
cd /home/pi/master
git clone git://github.com/adafruit/Adafruit_Python_ILI9341.git
cd Adafruit_Python_ILI9341
python setup.py install
echo 'configure system files'
cd /home/pi/master
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

