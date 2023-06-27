#!/bin/bash

yum install -y python3-requests python3.11-requests
python3 -m pip install --root-user-action=ignore ./termcolor/ 
