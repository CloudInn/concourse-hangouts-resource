#!/bin/sh
set -e
cd ./assets
cat ../testing/content.json | ./out
cat ../testing/bad-content.json | ./out || true && false
