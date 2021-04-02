#!/bin/sh
while true; do 
if git pull --dry-run | grep -q -v 'Already up-to-date.' && changed=1
then
sh staging.sh
fi
sleep 2m
done
