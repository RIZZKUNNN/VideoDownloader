#!/usr/bin/env bash
# Update dan install ffmpeg
apt-get update && apt-get install -y ffmpeg

# Install python dependencies
pip install -r requirements.txt
