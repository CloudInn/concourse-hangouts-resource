#!/bin/sh
set -e
cd ./assets
./out < ../testing/content.json
if ./out < ../testing/bad-content.json ; then
	false
else
	true
fi
