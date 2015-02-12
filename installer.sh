#!/bin/sh
echo "** podplayer installer **"
echo 'This will take a long time to run - time to grab a coffee (or even dinner).'
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
update-rc.d startradio defaults
cp sampleconfig.py config.py
chmod 666 config.py
echo 'Setting up wifi'
cp /etc/network/interfaces /etc/network/interfaces.bak
cp interfaces /etc/network
echo 'Fixing serial garbage.'
cp /boot/cmdline.txt /boot/cmdline.bak
cp cmdline.txt /boot
echo 'Setting up runtime environment'
chmod +x radio.py
mkdir log
echo '*************************'
echo 'You still need to:'
echo '1. update the keys in the config.py file'
echo '2. update the ip address and wifi key in /etc/network/interfaces.'

