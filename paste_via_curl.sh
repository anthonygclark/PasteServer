#!/bin/bash

# Code Syntax
TYPE=${1:-txt}
# Paste server address
HOST="$2"
# stdin
CODE=$(cat)

RES=$(curl -sS -d lang=${TYPE} --data-urlencode code="$CODE" -d submit "$HOST"/cmd)

if [[ ! -z "$RES" ]] ; then
    echo "${HOST}${RES}"
fi
