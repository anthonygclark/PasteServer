#!/usr/bin/env python2
#
# Simple form paster.
#
# Visit the form at / or...
# Use curl to post:
# curl -d lang=c -d code="test test test" -d submit http://localhost:8888/cmd
#

import sys
import hashlib
import subprocess
import io
import os
import shutil

from lib.pastie import HTMLPaster
from bottle import Bottle, route, get, post, request, run, static_file, redirect, template

class PasteServer(Bottle):
	class BottleHTML:
		''' HTML bottle templates for the Paste Server '''
		INDEX="""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Paster</title>

<link rel="stylesheet" href="{{statics}}/bootstrap.min.css">
<link rel="stylesheet" href="{{statics}}/bootstrap-theme.min.css">
<script src="{{statics}}/jquery.min.js"></script>
<script src="{{statics}}/bootstrap.min.js"></script>
</head>

<body>

<center><a href="/browse">Other Pastes</a></center>

<div class="container">
	<h2>
		{{pretext}}
	</h2>
	</br>

	<form action="/" role="form" method="post" class="form-horizontal" id="paste-form" name="paste-form">
		<!-- filename -->
		<div class="form-group">
			<label class="col-sm-2 control-label">Filename</label>
			<div class="col-sm-10">
				<p class="form-control-static">
				<input type="text" class="form-control" name="file" placeholder="hello_world.c">
				</p>
			</div>
		</div>

		<!-- Forced lang -->
		<div class="form-group">
			<label class="col-sm-2 control-label">
				<label><input type="checkbox" name="force_lang" id="force_lang"> Force Syntax</label>
			</label>
			<div class="col-sm-10">
				<select class="form-control" name="lang">
					% for lang in LANGS:
					<option value="{{lang}}"> {{lang}} </option>
					% end
				</select>
			</div>
		</div>

		<!-- Syntax Colors -->
		<div class="form-group">
			<label class="col-sm-2 control-label"> Highlighting Color</label>
			<div class="col-sm-10">
				<select class="form-control" name="color">
					% for color in COLORS:
					<option value="{{color}}"> {{color}} </option>
					% end
				</select>
			</div>
		</div>

		<!-- Code -->
		<div class="form-group">
			<label class="col-sm-2 control-label">Code</label>
			<div class="col-sm-10">
				<textarea class="form-control" id="code" name="code" rows="20" style="font-family:Courier New" placeholder="code here..."></textarea>
			</div>
		</div>

		<!-- Password -->
		<div class="form-group">
			<label class="col-sm-2 control-label">Password</label>
			<div class="col-sm-10">
				<input type="password" class="form-control" name="password" placeholder="Password">
				</p>
				<button type="submit" class="btn-lg btn-info btn-block" id="paste_it">Paste it!</button>
			</div>
		</div>
	</form>
</dev>
</body>
</html>
"""

		BADPW="""
<h2>
BAD PASSWORD
</h2>
"""

		QUICK_PASTE_INDEX="""\
<form action="/cmd" method="POST" accept-charset="UTF-8">
	File Type (e.g., c):
	<input type="text" name="lang">
	<br><br>
	Code:
	<br>
	<textarea name="code" cols="80" rows="24"></textarea>
	<br>
	<button type="submit">submit</button>
</form>
"""

		QUICK_PASTE_RET="""\
{{out}}
"""

		PASTE_DELETE="""\
Deleting <b>{{name}}</b> ... enter password to continue

<form action="{{path}}" method=POST>
	</br>Password: <input type="password" name="captcha">
	</br>
	</br><input type="submit" name="delete_it" value="Delete Paste">
	</br>
</form>
"""
	# end class BottleHTML

    # LANGS=($(for i in /usr/share/highlight/langDefs/* ; do echo $(basename $i .lang) ; done))
	# echo "LANGS = ["
	# for i in ${LANGS[@]}; do
	#	echo "\"$i\","
	# done
	# echo "]"
	''' Languages that highlight supports as of Mar. 2016 '''
	LANGS=[
			"abap4"     , "abc"     , "abnf"      , "actionscript" , "ada"      , "agda"         , "algol"      , "ampl"       , "amtrix"     , "applescript" , "arc"    , "ruby"     , "sas"
			"arm"       , "as400cl" , "ascend"    , "aspect"       , "asp"      , "assembler"    , "ats"        , "autohotkey" , "autoit"     , "avenue"      , "awk"    , "n3"       , "oz"
			"bat"       , "bbcode"  , "bcpl"      , "bibtex"       , "biferno"  , "bison"        , "blitzbasic" , "bms"        , "bnf"        , "boo"         , "ceylon" , "charmm"   , "scala"
			"chill"     , "c"       , "clean"     , "clearbasic"   , "clipper"  , "clojure"      , "clp"        , "cobol"      , "coldfusion" , "crk"         , "csharp" , "scilab"   , "sh"
			"css"       , "dart"    , "diff"      , "d"            , "dylan"    , "ebnf"         , "eiffel"     , "erlang"     , "euphoria"   , "express"     , "fame"   , "felix"    , "fortran77"
			"fortran90" , "frink"   , "fsharp"    , "fx"           , "gambas"   , "gdb"          , "go"         , "graphviz"   , "haskell"    , "haxe "       , "hcl"    , "html"     , "httpd"
			"icon"      , "idlang"  , "idl"       , "inc_luatex"   , "informix" , "ini"          , "innosetup"  , "interlis"   , "io "        , "jasmin"      , "java"   , "js"       , "ps1"
			"jsp"       , "ldif"    , "lhs"       , "lilypond"     , "limbo"    , "lindenscript" , "lisp"       , "logtalk"    , "lotos"      , "lotus"       , "lua"    , "luban"    , "ps"
			"make"      , "maple"   , "matlab"    , "maya"         , "mercury"  , "miranda"      , "mod2"       , "mod3"       , "modelica"   , "moon"        , "ms"     , "mssql"    , "mxml"
			"nasal"     , "nbc"     , "nemerle"   , "netrexx"      , "nice"     , "nsis"         , "nxc"        , "oberon"     , "objc"       , "ocaml"       , "octave" , "oorexx"   , "os"
			"paradox"   , "pas"     , "pdf"       , "perl"         , "php"      , "pike"         , "pl1"        , "plperl"     , "plpython"   , "pltcl"       , "pov"    , "progress" , "pro"
			"psl"       , "pure"    , "pyrex"     , "python"       , "q"        , "qmake"        , "qu"         , "rebol"      , "rexx"       , "r"           , "rnc"    , "rpg"      , "rpl"
			"s"         , "small"   , "smalltalk" , "sml"          , "snmp"     , "snobo;"       , "spec"       , "spn"        , "sql"        , "squirrel"    , "swift"  , "sybase"   , "tcl"
			"tsql"      , "ttcn3"   , "txt"       , "upc"          , "vala"     , "vb"           , "verilog"    , "vhd"        , "xml"        , "xpp"         , "yaiff"  , "yang"     , "znn"
            "tcsh"      , "tex"     , "ts"
	]

	COLORS = HTMLPaster.HighlightProcess.STYLES

	def __init__(self, runtime_dir, password):
		super(PasteServer, self).__init__()
		self.name = "Paste Bottle"
		self.paste_dir = os.path.join(runtime_dir, "pastes")
		self.static_dir = os.path.join(runtime_dir, "static")
		self.password = hashlib.md5(password).hexdigest()

		self.paster = HTMLPaster(self.paste_dir, "/static" , "/static")

		self.route('/'                                , method='GET'  , callback=self.paste_index)
		self.route('/'                                , method='POST' , callback=self.paste_post)
		self.route('/badpw'                           , method='GET'  , callback=self.bad_pass)
		self.route('/cmd'                             , method='GET'  , callback=self.cmd_index)
		self.route('/cmd'                             , method='POST' , callback=self.paste_post_from_cmd)
		self.route('/static/<filepath>'               , method='GET'  , callback=self.javascript_css_getter)
		self.route('/browse'                          , method='GET'  , callback=self.browse_pastes)
		self.route('/browse/<paste_path>/delete-form' , method='GET'  , callback=self.paste_delete)
		self.route('/browse/<paste_path>/delete-form' , method='POST' , callback=self.paste_delete_form)
		self.route('/browse/<paste_path>/<index>'     , method='GET'  , callback=self.paste_view)


	def get_dir_list(self):
		dirs = os.listdir(self.paste_dir)
		link_str = '</br><a href="/browse/{paste}/index.html">{paste}</a>'
		return [link_str.format(paste=i) for i in dirs] or ['None']


	def paste_index(self):
		''' Creates a template for the main paste form '''
		return template(self.BottleHTML.INDEX, pretext='', statics="/" + self.static_dir,
				LANGS=self.LANGS, COLORS=self.COLORS)


	def bad_pass(self):
		''' Creates a template for when an incorrect password is entered '''
		return template(self.BottleHTML.BADPW)


	def cmd_index(self):
		''' Creates a template for the simple/command line form '''
		return template(self.BottleHTML.QUICK_PASTE_INDEX)


	def paste_post_from_cmd(self):
		''' Post handler for the simple/command line form. Renders a template
			containing the result URL from the paste
		'''
		style = 'kellys'
		code = request.forms.get('code')
		lang = request.forms.get('lang')
		fname = self.paster.id_generator()

		if lang:
			fname = fname + "." + lang

		self.paster.highlight_file(io.BytesIO(code), fname, style, lang)

		dest = '/browse/' + os.path.basename(self.paster.output_dir) + '/index.html'

		return template(self.BottleHTML.QUICK_PASTE_RET, out=dest)


	def paste_post(self):
		''' Post handler for the main paste form. Redirects to
			the resulting paste index.
		'''
		fname = request.forms.get('file')
		code = request.forms.get('code')
		style = request.forms.get('color')
		lang = ''

		## XXX unsafe, password in memory, right?
		password = request.forms.get('password')
		m = hashlib.md5()
		m.update(password or '')
		del password

		if m.hexdigest() != self.password:
			redirect('/badpw')

		if request.forms.get('force_lang'):
			lang = request.forms.get('lang')

		self.paster.highlight_file(io.BytesIO(code), fname, style, lang)
		redirect('/browse/' + os.path.basename(self.paster.output_dir) + '/index.html')


	def javascript_css_getter(self, filepath):
		''' Static file server for JS and CSS files '''
		return static_file(filepath, root=self.static_dir)


	def browse_pastes(self):
		''' Simple dir list GET handler '''
		return self.get_dir_list()


	def paste_delete(self, paste_path):
		''' Returns a template form for deleting a paste '''
		return template(self.BottleHTML.PASTE_DELETE, name=paste_path,
				path='/browse/' + paste_path + '/delete-form')


	def paste_delete_form(self, paste_path):
		''' Post handler for deleting a paste '''
		_path = os.path.join(self.paste_dir, paste_path)
		try:
			shutil.rmtree(_path)
		except OSError as e:
			print e

		redirect('/')


	def paste_view(self, paste_path, index):
		''' Renders the INDEX of a paste '''
		return static_file(paste_path + '/' + index, root=self.paste_dir)


if __name__ == '__main__':
	run_host = '127.0.0.1'
	run_port = 8888
	password = ''

	if len(sys.argv) > 1:
		run_host = sys.argv[1]
	if len(sys.argv) > 2:
		run_port = sys.argv[2]
	if len(sys.argv) > 3:
		password = sys.argv[3]

	service = PasteServer("./", password)

	service.run(host=run_host, port=run_port)

