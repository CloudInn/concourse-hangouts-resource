#!/bin/sh
set -e
cd ./assets

./out < ../testing/content.json
./in < ../testing/content.json
./check < ../testing/content.json

if ./out < ../testing/bad-config.json ; then
	false
else
	true
fi

if ./out < ../testing/bad-url.json ; then
	false
else
	true
fi
