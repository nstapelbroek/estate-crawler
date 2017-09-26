#!/usr/bin/sh
while :
do
  echo "Starting run"
  ./crawler.py
  echo "Run completed, waiting 12600 seconds before next run"
  sleep 12600
done