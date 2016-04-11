#!/usr/bin/env python2

import sys
import os
from bottle import run
from Paster import Paster

run_host = '127.0.0.1'
run_port = 8888
password = ''

def usage():
	print "paste_bottle [local address] [port] [password]"
	print "     address will default to 127.0.0.1"
	print "     port will default to 8888"
	print "     password will default to empty/blank"


if len(sys.argv) > 1:
	if sys.argv[1] in ('-h', '--help', '-H', '--HELP'):
		usage()
		sys.exit(0)

	run_host = sys.argv[1]

if len(sys.argv) > 2:
	run_port = sys.argv[2]

if len(sys.argv) > 3:
	password = sys.argv[3]

service = Paster(os.path.realpath(os.path.dirname(sys.argv[0])), password)

service.run(host=run_host, port=run_port)

