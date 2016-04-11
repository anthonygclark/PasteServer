#!/bin/bash

# readlink and osx TODO
cd $(dirname $(readlink -f $0))

python2 -m paste_bottle "$@"
