#!/bin/bash
python3 -m venv venv
sudo apt-get install libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0 -y
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt