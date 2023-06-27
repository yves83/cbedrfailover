#!/bin/bash

rsync -avz --delete --exclude='*.conf' /root/EDRHA/ root@192.168.200.45:/root/EDRHA/
#rsync -avz --delete  /root/EDRHA/ root@192.168.200.44:/root/EDRHA/
