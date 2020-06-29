#!/bin/sh

RC_LOCAL='/etc/rc.local'
#RC_LOCAL='/home/pi/finishline/rc.local'

if ! grep -Fq 'derby_race.py' $RC_LOCAL; 
then
    sed -i '$ i python3 /home/pi/finishline/derby_race.py' $RC_LOCAL
fi