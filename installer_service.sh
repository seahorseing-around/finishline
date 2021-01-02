#!/bin/sh

# install basics
apt-get install vim -y
pip install statistics

#Add service file & relead systemctl
echo "Copy in Service file"
cp derby_race.service /lib/systemd/system/derby_race.service
echo "Reload Systemd Daemon"
sudo systemctl daemon-reload
#auto-start on startup
echo "Enable derby_race service to autostart on startup"
sudo systemctl enable derby_race
#start & check status
echo "Start derby_race service"
sudo service derby_race start
sudo service derby_race status

#Add restart button
RC_LOCAL='/etc/rc.local'

if ! grep -Fq 'restart_button.py' $RC_LOCAL; 
then
    sed -i '$ i python3 /home/pi/finishline/restart_button.py' $RC_LOCAL
fi
