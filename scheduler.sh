#!/bin/bash
echo "scheduler triggered" >> /home/user/scheduler.log
cd ~/rewards-sender
/usr/bin/yarn start
sleep 10m
cd ~/
/usr/bin/python3 auto_sell.py