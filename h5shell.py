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
class Colour:
	PROMPT1 = '\033[22;32m'
	PROMPT2 = '\033[1;32m'
	STATS = '\033[1;33m'
	GROUP = '\033[1;34m'
	DATASET = '\033[0;37m'
	DATATYPE = '\033[1;35m'
	ERROR = '\033[31m'
	END = '\033[m'

	def disable(self):
		self.PROMPT1 = ''
		self.PROMPT2 = ''
		self.GROUP = ''
		self.DATASET = ''
		self.DATATYPE = ''
		self.ERROR = ''
		self.END = ''


# Pretty formatting of shape array:
def shapeformat (shape):
	if shape == ():
		return 'Scalar'
	else:
		return 'x'.join([str(i) for i in shape])


# Display formatted list of objects contained in the given group:
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

		keyobj = h5group[key]

		if isinstance(keyobj, h5.Group):

			# Display GROUP info:
			keystr = Colour.GROUP + key + '/' + Colour.END

		elif isinstance(keyobj, h5.Dataset):

			# Check for compound datatypes:
			if keyobj.dtype.isbuiltin != 1:
				dtypestr = 'Compound'
			else:
				dtypestr = str(keyobj.dtype)

			# Display DATASET info:
			keystr = Colour.DATASET + '{0:-<40s}'.format(key+' ') + Colour.END
			keystr += Colour.STATS
			keystr += ' {0:^10s} {1:^10s} '.format(dtypestr,shapeformat(keyobj.shape))

		else:

			# Display DATATYPE info:
			keystr = Colour.DATATYPE + key + '+' + Colour.END

		print keystr
	

# Application class:
class H5Cmd(Cmd):
	
	intro = "h5shell v1.0.  Type '?' for list of commands.\n"

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

	def do_emptyline(self):
		pass

	def default(self, line):
		errstr = "*** Invalid command. Type '?' for list of valid commands."
		print Colour.ERROR + errstr + Colour.END

	def do_EOF(self, arg):
		print '\nExiting...'
		return True

	def do_quit(self, arg):
		print 'Exiting...'
		return True


	# Inline help methods:

	def do_help(self, arg):

		if arg == '':
			print """Shell Commands (help <topic> for more info):
============================================
ls	[path]	List contents of group.
cd	[group]	Change current group.
!	<cmd>	Execute command in system shell.

quit		Exits h5shell.
============================================
"""
		else:
			switch = {
					'ls': self.help_ls,
					'cd': self.help_cd,
					'!': self.help_shell,
					'quit': self.help_quit
					}
			if arg in switch.keys():
				switch.get(arg)()
			else:
				print Colour.ERROR + "*** No help on '{0}'.\n".format(arg) + Colour.END

	def help_ls (self):
		print """Usage: ls [path]

Lists contents of current group or specified [path].  Wildcards are
accepted.  For example, "ls /foo*" will list all objects whose names
match with the prefix "pref" in the root group.  Similarly, "ls ?bar"
will list all objects in the current group whose names are 4
characters long and end with "bar".
"""

	def help_cd (self):
		print """Usage: cd [group]

Changes the current group to [group] or to '/' if [group] is absent.
"""

	def help_shell (self):
		print """Usage: ! <cmd>

Executes the given command in your default system shell.
"""

	def help_quit (self):
		print """Usage: quit

Exits h5shell. EOF (^D) can also be used.
"""


	# Methods for internal use:

	# Set command prompt:
	def set_prompt(self):

		pathstr = self.pathstr
		if len(pathstr)>1:
			pathstr = pathstr.rstrip('/')

		self.prompt = Colour.PROMPT1
		self.prompt += self.fname + ':'
		self.prompt += Colour.PROMPT2
		self.prompt += pathstr
		self.prompt += Colour.PROMPT1
		self.prompt += '> '
		self.prompt += Colour.END


	# Convert relative path names to absolute:
	def rel_to_absolute(self, relpath):

		# Convert path:
		if len(relpath)>0 and relpath[0] == '/':
			abspath = relpath
		else:
			abspath = self.pathstr + relpath

		# Modify behaviour of ..:
		if abspath.endswith('..'):
			abspath += '/'

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

		# Convert relative paths to absolute:
		text = self.rel_to_absolute(text)

		# Split path and (possibly incomplete) group name:
		grpPath, grpName = text.rsplit('/',1)

		# Normalise group name:
		grpPath = grpPath.rstrip('/') + '/'

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
			print Colour.ERROR + "*** Path '{0}' is not a group.".format(newpathstr) + Colour.END
		else:
			self.pathstr = newpathstr
			self.set_prompt()

	# List group contents:
	def do_ls(self, lspath):

		# Convert relative paths to absolute:
		lspath = self.rel_to_absolute(lspath)

		# Split path and name of object:
		grpPath, grpName = lspath.rsplit('/',1)

		# Normalise group name:
		grpPath = grpPath.rstrip('/') + '/'

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

	# Start command loop:
	c = H5Cmd(f, h5fname)
	c.cmdloop()

	# Close h5 file:
	f.close()
