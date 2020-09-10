#!/bin/sh
set -e
cd ./assets
BR_YELLOW='\e[0;93m'
RESET='\e[0m'

echo -e "${BR_YELLOW}Testing out sunny day with URL...${RESET}"
./out / < ../testing/with-url.json
echo

echo -e "${BR_YELLOW}Testing out sunny day without URL...${RESET}"
./out / < ../testing/no-url.json
echo

echo -e "${BR_YELLOW}Testing out sunny day URL not specified...${RESET}"
./out / < ../testing/basic.json
echo

echo -e "${BR_YELLOW}Testing in sunny day...${RESET}"
./in / < ../testing/basic.json
echo

echo -e "${BR_YELLOW}Testing check sunny day...${RESET}"
./check / < ../testing/basic.json
echo

echo -e "${BR_YELLOW}Testing out bad config...${RESET}"
if ./out / < ../testing/bad-config.json ; then
	false
else
	true
fi
echo

echo -e "${BR_YELLOW}Testing out bad url...${RESET}"
if ./out / < ../testing/bad-url.json ; then
	false
else
	true
fi
echo
