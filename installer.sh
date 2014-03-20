#!/bin/sh
echo "** radio installer **"
echo "apt-get update"
apt-get update
echo
echo "apt-get -y upgrade"
apt-get -y upgrade
echo
echo "apt-get -y install python-pip"
apt-get -y install python-pip
echo
echo 'pip installs...'
pip install beautifulsoup4 requests python-mpd2 logging feedparser urllib3
echo
echo "apt-get -y install python-serial"
apt-get -y install python-serial mpd mpc	
cp mpd.conf /etc
cp startradio /etc/init.d
chmod 755 /etc/init.d/startradio
update-rc.d startradio defaults
cp sampleconfig.py config.py
echo
echo 'Setting up wifi'
cp /etc/network/interfaces /etc/network/interfaces.bak
cp interfaces /etc/network
echo 'Fixing serial garbage.'
cp /boot/cmdline.txt /boot/cmdline.bak
cp cmdline.txt /boot
echo
chmod +x radio.py
mkdir log
echo '*************************'
echo 'You still need to:'
echo '1. update the keys in the config.py file'
echo '2. update the ip address and wifi key in /etc/network/interfaces.'

