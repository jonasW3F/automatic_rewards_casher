#!/bin/bash
echo "scheduler triggered" >> /home/usr/scheduler.log
cd ~/rewards-sender
usr/bin/yarn start
sleep 300
cd ~/
usr/bin/python3 kraken_sell.py

