#!/usr/bin/env python

import h5py as h5

#### Standard Library Modules ####
import readline
from cmd import Cmd

from sys import argv, exit
from os import path, system

import re
##################################

# Define ANSI escape sequences for use in colour mode:
class Colors:
	PROMPT = '\033[32m'
	GROUP = '\033[1;34m'
	DATASET = '\033[1;37m'
	END = '\033[m'

	def disable(self):
		self.PROMPT = ''
		self.GROUP = ''
		self.DATASET = ''
		self.END = ''


# Display list of objects contained in the given group:
def list_objects(h5group, matchstr):

	# Convert common filename matching wildcards with regexp equivalents:
	if len(matchstr)>0:
		restr = '^' + matchstr.replace('.','\.').replace('?','.').replace('*','.*') + '$'
	else:
		restr = ''

	for key in h5group.keys():

		# Skip object if it's key doesn't match regexp:
		if re.search(restr, key) == None:
			continue

		keystr = key
		if isinstance(h5group[key], h5.Group):
			keystr = Colors.GROUP + keystr + '/' + Colors.END
		else:
			keystr = Colors.DATASET + keystr + Colors.END

		print keystr


# Application class:
class H5Cmd(Cmd):

	prompt = 'HDF5> '

	# Constructor:
	def __init__(self, f, fname):

		# Call parent constructor:
		Cmd.__init__(self)

		# Record handle to h5 file:
		self.f = f
		self.fname = fname

		# Set initial group to /:
		self.do_cd('/')

		# Remove / from readline completer delimiter list:
		delims = readline.get_completer_delims().replace('/','')
		readline.set_completer_delims(delims)


	# House-keeping methods:

	def do_shell(self, arg):
		system(arg)

	def do_emptyline(self, arg):
		pass

	def do_EOF(self, arg):
		print '\nExiting...'
		return True

	def do_quit(self, arg):
		print 'Exiting...'
		return True


	# Internal database navigation methods:

	# Convert relative path names to absolute:
	def rel_to_absolute(self, relpath):

		# Convert path:
		if len(relpath)>0 and relpath[0] == '/':
			abspath = relpath
		else:
			abspath = self.pathstr + relpath

		# Clean up:
		while '//' in abspath:
			abspath = abspath.replace('//','/')

		# Evaluate parent group markers:
		pathList = abspath.split('/')
		while '..' in pathList:
			idx = pathList.index('..')
			if idx > 1:
				del pathList[(idx-1):(idx+1)]
			else:
				del pathList[1]

		abspath = '/'.join(pathList)

		return(abspath)


	# Generic path name completion:
	def path_completion(self, text):
		
		if len(text) == 0:
			text = self.pathstr
		elif text[0] != '/':
			text = self.pathstr + text

		if text.endswith('..'):
			grpPath, grpName = text, ''
		else:
			grpPath, grpName = text.rsplit('/',1)

		# Normalise group name:
		grpPath = grpPath.rstrip('/') + '/'

		# Convert relative paths to absolute:
		grpPath = self.rel_to_absolute(grpPath)

		# Return if no group at chosen path:
		if not isinstance(self.f[grpPath], h5.Group):
			return []

		result = []

		for key in self.f[grpPath].keys():

			if not isinstance(self.f[grpPath][key], h5.Group):
				continue

			if key.startswith(grpName):
				result.append(grpPath + key)

		return result


	# Database navigation commands:

	# Change directory:
	def do_cd(self, newpathstr):

		# Normalise group name:
		newpathstr = newpathstr.rstrip('/') + '/'

		# Convert relative paths to absolute:
		newpathstr = self.rel_to_absolute(newpathstr)

		# Check that newpathstr refers to an extant group:
		if f.get(newpathstr, getclass=True) != h5.Group:
			print "Error: Path '{0}' is not a group.".format(newpathstr)
		else:
			self.pathstr = newpathstr
			if len(self.pathstr)>1:
				self.prompt = Colors.PROMPT
				self.prompt += self.fname + ': ' + newpathstr.rstrip('/') + '> '
				self.prompt += Colors.END
			else:
				self.prompt = Colors.PROMPT
				self.prompt += self.fname + ': ' + newpathstr + '> '
				self.prompt += Colors.END

	# List group contents:
	def do_ls(self, lspath):

		if len(lspath) == 0:
			lspath = self.pathstr
		elif lspath[0] != '/':
			lspath = self.pathstr + lspath

		if lspath.endswith('..'):
			grpPath, grpName = lspath, ''
		else:
			grpPath, grpName = lspath.rsplit('/',1)

		# Normalise group name:
		grpPath = grpPath.rstrip('/') + '/'

		# Convert relative paths to absolute:
		grpPath = self.rel_to_absolute(grpPath)

		# Error if group path invalid:
		if not isinstance(self.f[grpPath], h5.Group):
			print Colour.ERROR + 'Invalid path: %s' % (grpPath) + Colour.END
			return

		list_objects(self.f[grpPath], grpName)
	


	def complete_cd(self, text, line, begidx, endidx):
		return self.path_completion(text)

	def complete_ls(self, text, line, begidx, endidx):
		return self.path_completion(text)


### MAIN ###
if __name__ == '__main__':

	# Parse command line:
	if len(argv) < 2:
		print "Usage: %s datafile\n" % (path.basename(argv[0]))
		exit(0)
	h5fname=argv[1]

	# Inform about the creation of a new file:
	if not path.exists(h5fname):
		print "Error: File '%s' does not exist. Aborting.\n" % (h5fname)
		exit(1)
	
	# Open h5 file:
	try:
		f = h5.File(h5fname)
	except IOError:
		print "Error opening HDF5 file '%s'. Aborting." % (h5fname)
		print "(Do you have write access to this location?)"
		exit(1)
	
	# Assemble header:

	# Start command loop:
	c = H5Cmd(f, h5fname)
	c.cmdloop()

	# Close h5 file:
	f.close()
