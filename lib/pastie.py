#!/usr/bin/env python2
# 
# A static code paste generator. 
# Currently depends on bootstrap for divs and labels.
#

import sys
import datetime
import subprocess
import string
import random
import os
import io
import shutil


###############################################
################## HTML OUTPUT ################
###############################################
class HTMLPaster:
	"""
	Creates a webpage, or series of web pages, containing
	pasted code.

	"""
	
	class HTMLConstants:
		"""
		Constants for HTML. This will wrap the output of `highlight`
		"""
		HEADER="""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name}</title>

<!-- Bootstrap -->
<link rel="stylesheet" href="{css_dir}/bootstrap.min.css">
<link rel="stylesheet" href="{css_dir}/bootstrap-theme.min.css">
<script src="{javascript_dir}/jquery.min.js"></script>
<script src="{javascript_dir}/bootstrap.min.js"></script>

</head>
<body style="padding: 10px 50px 10px 50px; background-color: #6D6D6D;">
"""

		DIV_WRAPPER="""\
<div class="panel panel-default">
	<div class="panel-heading">
		<h3 class="panel-title">{name}</h3>
	</div>
	<div class="panel-body">
		<a style="text-decoration: none !important;" href="{name}"><span class="label label-info">Download</span></a>
		<a style="text-decoration: none !important;" href="./delete-form"><span class="label label-danger">Delete</span></a>
		|
		<span class="label label-success">{extension}</span>
		<span class="label label-default">{size}</span>
		<span class="label label-default">{date}</span> 


		<div class="pull-right" style="padding-right:30px">
			<div class="btn-group">
				<button class="btn btn-primary btn-xs dropdown-toggle" type="button" data-toggle="dropdown">Color: %s  <span class="caret"></span>
				</button>
				<ul class="dropdown-menu" role="menu">
					{styles}
				</ul>
			</div>
		</div>

	</div>
</div>
<div class="well">
"""

		STYLE_MENU_ITEM="<li><a href=\"{1}\">{0}</a></li>\n"

		FOOTER="""\
</div>
</body>
</html>
"""
	# end class HTMLConstants


	class HighlightProcessException(Exception):
		def __init__(self, message):
			super(HTMLPaster.HighlightProcessException, self).__init__(message)


	class HighlightProcess:
		HLCMD ='highlight'

		STYLES = [ 
                'kellys'         , 'bclear'          , 'molokai' , 'nightshimmer' ,
				'solarized-dark' , 'solarized-light' , 'night'   ,
				'bright'         , 'camo'            , 'clarity' , 'darkblue'     ,
				'darkspectrum'   , 'freya'           , 'fruit'   ,
				'kellys'         , 'matrix'          , 'print'   , 'zenburn' 
        ]
		
		# Can be appended to. Can still take outputs, etc
		HL_DEFAULT_ARGS = '--style={style} -S {extension} -I --inline-css -K 9 -l -f --enclose-pre --replace-tabs=4 --anchors -y line'
		DEFAULT_STYLE = STYLES[0]

		@classmethod
		def run(cls, extension, _stdin, _stdout, _stderr, *hlargs):
			# insert default style and extension
			hl_defaults = cls.HL_DEFAULT_ARGS\
							.format(style = cls.DEFAULT_STYLE, extension = extension)
			# listify
			cmd = [cls.HLCMD] + list(hl_defaults.split(' '))
			for i in list(hlargs): cmd.append(i)
		
			# create the process
			proc = subprocess.Popen(' '.join(cmd), shell=True, stdin=subprocess.PIPE, 
									stdout=subprocess.PIPE,
									stderr=subprocess.PIPE, bufsize=-1)
			# read stderr	
			stdout, stderr = proc.communicate(_stdin.getvalue())
			ret = proc.returncode
			# throw it if there is stuff in stderr or return code isnt 0
			if stderr or ret != 0:
				raise HTMLPaster.HighlightProcessException('Exit code: {} - '.format(ret) + stderr)

			_stdout.write(stdout)
			return True


	def __init__(self, paste_root, js_location, css_location):
		assert paste_root
		self.paste_root = paste_root
		self.js_location = js_location
		self.css_location = css_location


	def id_generator(self, s=4):
		chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
		return ''.join(random.choice(chars) for x in range(s))


	# This is here since we really only care about a nice name 
	# when presenting it. More should be added.
	def get_extension_type(self, ext):
		return {
			"c"   : "C",
			"py"  : "Python",
			"cu"  : "Cuda",
			"cuh" : "Cuda Header",
			"cpp" : "C++",
			"cc"  : "C++",
			"C"   : "C++",
			"hh"  : "C++-Header",
			"rb"  : "Ruby",
			"sh"  : "Bash",
			"bat" : "Batch",
			"h"   : "C-Header",
			"m"   : "Objective-C",
			"js"  : "JavaScript",
			"s"   : "Assembly",
			"lsp" : "LISP",
			"txt" : "Plain-Text",
		}.get(ext, ext.upper())


	def added_extension(self, ext):
		return {
			"cu" : "c"
		}.get(ext, ext)


	@staticmethod
	def get_size_impl(size_in_bytes):
		factors = ((1<<50L, 'PB'),
				(1<<40L, 'TB'),
				(1<<30L, 'GB'),
				(1<<20L, 'MB'),
				(1<<10L, 'KB'),
				(1, 'B'))

		for factor, suffix in factors:
			if size_in_bytes >= factor:
				break

		return '%.2f %s' % (size_in_bytes/float(factor), suffix)


	def get_file_size(self, path):
		size = float(os.stat(path).st_size)
		return HTMLPaster.get_size_impl(size)


	def get_size_from_bytes(self, _bytes):
		return HTMLPaster.get_size_impl(_bytes)


	def make_directory_structure(self, path, pname):
		assert len(path)
		assert len(pname) 
		
		dir_name = os.path.join(path, "PASTE-%s-%s" % (self.id_generator(), pname))
		os.mkdir(dir_name)
		return dir_name


	def highlight_file(self, inputbytes, name, style=None, ext=None):
		'''
		Runs the highlight command on the inputbytes creating a file called 'name'
		with style 'style'. The 'ext' arg can be used to force syntax matching for 
		files without extensions for example - or if you want to force some mismatch.

		A directory is created with the named file and a myriad series of index.html
		files for each color style where the argument 'style' is index.html.
		'''
		assert len(name)

		# create lookup tables
		main_style = style or HTMLPaster.HighlightProcess.DEFAULT_STYLE
		main_index = 'index.html'

		styles = [main_style]
		styles = filter(lambda x: x != main_style, HTMLPaster.HighlightProcess.STYLES)
		indices = {s:'index-{}.html'.format(s) for s in styles}
		indices[main_style] = main_index 

		# Create ordered menu items
		styles_menu = [HTMLPaster.HTMLConstants.STYLE_MENU_ITEM.format(main_style, main_index)]

		for s,i in indices.items():
			styles_menu.append(HTMLPaster.HTMLConstants.STYLE_MENU_ITEM.format(s, i))

		# create and return the destination directory
		self.output_dir = self.make_directory_structure(self.paste_root, name)

		# These functions will both get a nice name for the format, and, if
		# possible, link some file extension or specified extension/type to another.
		# For example, test.cu will fail the highlight process as .cu isnt a valid format.
		# Since we know .cu (CUDA) files are C-like, we create a mapping to .c and give 
		# it the name CUDA.
		#
		#	See self.added_extension and self.get_extension_type
		#
		# create pretty extension from the actual type of file
		pretty_ext = self.get_extension_type(ext or os.path.splitext(name)[1][1:] or 'txt')
		# normalize extension, if we have to.
		ext = self.added_extension(ext or os.path.splitext(name)[1][1:] or 'txt')
		
		# get current time
		date = datetime.datetime.now().strftime('%A, %b %d, %Y %I:%M%p')
		
		# Write the file to disk
		with open(os.path.join(self.output_dir, name), 'w+') as downloadable:
			downloadable.write(inputbytes.getvalue())

		# create a formatted header
		header = HTMLPaster.HTMLConstants.HEADER.format(name=name,
				javascript_dir=self.js_location,
				css_dir=self.css_location)

		footer = HTMLPaster.HTMLConstants.FOOTER

		# create mostly formatted div
		div = HTMLPaster.HTMLConstants.DIV_WRAPPER.format(name=name, 
				extension=pretty_ext,
				size=self.get_size_from_bytes(len(inputbytes.getvalue())),
				date=date, styles='\n'.join(styles_menu))

		# Create an index for all of the non-default styles
		for s,i in indices.items():
			# get an output html path
			dest = os.path.join(self.output_dir, i)
			
			# create and write to the html file
			with open(dest, 'w+') as outputfile:
				outputfile.write(header)
				outputfile.write(div % s)
				
				try:
					HTMLPaster.HighlightProcess.run(ext, inputbytes, outputfile,
							subprocess.PIPE, '--style=%s' % s)
				except HTMLPaster.HighlightProcessException as e:
					# Fatal, stop writing.
					shutil.rmtree(self.output_dir)
					raise e

				outputfile.write(footer)



###############################################
############# TEST ENTRY POINT ################
###############################################
if __name__ == '__main__':
	import argparse

	parser = argparse.ArgumentParser(description='Pastie - A Simple Paste Service')
	parser.add_argument('-n', type=str, help='Name to give paste', required=True, dest='name')
	parser.add_argument('-s', type=str, help='Syntax Color Style', dest='style')
	parser.add_argument('-t', type=str, help='Forced file-type', dest='type')
	args = parser.parse_args()
	
	_name = args.name
	_style= args.style
	_type = args.type
	
	if sys.stdin.isatty():
		print 'Not interactive!'
		print 'Pipe data to this process'
		sys.exit(2)
	
	PASTE_DIR  = os.path.join(os.path.expanduser('~'), 'web/paste')
	
	# Create the highlighter
	html = HTMLPaster(PASTE_DIR, "../../static", "../../static")
	stdin = io.BytesIO(sys.stdin.read());
	
	html.highlight_file(stdin, _name, style=_style, ext=_type)

	# Print the url ... important for parsers of output
	print "{}".format(os.path.basename(html.output_dir))
