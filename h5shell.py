#!/usr/bin/env python

"""
h5shell v1.1

Copyright 2011 Tim Vaughan

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

__version__ = '1.1'

import h5py as h5

#### Standard Library Modules ####
import readline
from cmd import Cmd

from sys import argv, exit
from os import path, system
from argparse import ArgumentParser

import re
##################################

class Colour:
	"""Define ANSI escape sequences for use in colour mode."""

	PROMPT1 = '\033[22;32m'
	PROMPT2 = '\033[1;32m'
	STATS = '\033[1;33m'
	GROUP = '\033[1;34m'
	ATTR = '\033[1;36m'
	DATASET = '\033[0;37m'
	DATATYPE = '\033[1;35m'
	ERROR = '\033[31m'
	END = '\033[m'
	
	def __init__(self, no_colour):
		if no_colour:
			self.disable()

	def disable(self):
		"""Disable ANSI colour sequences."""

		self.PROMPT1 = ''
		self.PROMPT2 = ''
		self.STATS = ''
		self.GROUP = ''
		self.ATTR = ''
		self.DATASET = ''
		self.DATATYPE = ''
		self.ERROR = ''
		self.END = ''


def shapeformat (shape):
	"""Pretty formatting of shape array."""

	if shape == ():
		return 'Scalar'
	else:
		return 'x'.join([str(i) for i in shape])


def list_objects(h5group, matchstr, colour):
	"""Display formatted list of objects contained in the given group."""

	# Convert common filename matching wildcards with regexp equivalents:
	if len(matchstr)>0:
		restr = '^' + matchstr.replace('.','\.').replace('?','.').replace('*','.*') + '$'
	else:
		restr = ''
	
	# List matching group attributes:
	for key in h5group.attrs:

		# Skip object if its key doesn't match regexp:
		if re.search(restr, key) == None:
			continue

		keyobj = h5group.attrs[key]

		# Check for compound datatypes:
		if keyobj.dtype.isbuiltin != 1:
			dtypestr = '(Compound)'
		else:
			dtypestr = '(' + str(keyobj.dtype) + ')'

		keystr = colour.ATTR + '{0:-<40s}'.format('@'+key+' ') + colour.END

		keystr += colour.STATS
		if keyobj.size == 1:
			keystr += ' ={0:<10s} {1:^10s} '.format(str(keyobj[0]), dtypestr)
		else:
			keystr += ' {0:^10s} {1:^10s} '.format(shapeformat(keyobj.shape), dtypestr)
		keystr += colour.END

		print keystr

	# List matching group objects:
	for key in h5group:

		# Skip object if its key doesn't match regexp:
		if re.search(restr, key) == None:
			continue

		keyobj = h5group[key]

		if isinstance(keyobj, h5.Group):

			# Display GROUP info:
			keystr = colour.GROUP + key + '/' + colour.END

		elif isinstance(keyobj, h5.Dataset):

			# Check for compound datatypes:
			if keyobj.dtype.isbuiltin != 1:
				dtypestr = '(Compound)'
			else:
				dtypestr = '(' + str(keyobj.dtype) + ')'

			# Display DATASET info:
			keystr = colour.DATASET + '{0:-<40s}'.format(key+' ') + colour.END
			keystr += colour.STATS
			keystr += ' {0:^10s} {1:^10s} '.format(shapeformat(keyobj.shape), dtypestr)
			keystr += colour.END

		else:

			# Display DATATYPE info:
			keystr = colour.DATATYPE + '+' + key + colour.END

		print keystr
	

class H5Cmd(Cmd):
	"""Application class."""
	
	intro = """h5shell v{:s}
Copyright 2011 Tim Vaughan

This program comes with ABSOLUTELY NO WARRANTY.  This is free
software, and you are welcome to redistribute it under certain
conditions.  Type 'license' for details.

Type '?' for a full list of commands.\n""".format(__version__)

	def __init__(self, f, fname, colour):

		Cmd.__init__(self)

		# Record handle to h5 file:
		self.f = f
		self.fname = fname
		
		# Record preferred colours:
		self.colour = colour

		# Set initial group to /:
		self.do_cd('/')


	# House-keeping methods:

	def set_prompt(self):
		"""Set command prompt."""

		pathstr = self.pathstr
		if len(pathstr)>1:
			pathstr = pathstr.rstrip('/')

		self.prompt = self.colour.PROMPT1
		self.prompt += self.fname + ':'
		self.prompt += self.colour.PROMPT2
		self.prompt += pathstr
		self.prompt += self.colour.PROMPT1
		self.prompt += '> '
		self.prompt += self.colour.END

	def do_shell(self, arg):
		system(arg)

	def do_emptyline(self):
		pass

	def default(self, line):
		errstr = "*** Invalid command. Type '?' for list of valid commands."
		print self.colour.ERROR + errstr + self.colour.END

	def do_EOF(self, arg):
		print '\nExiting...'
		return True

	def do_quit(self, arg):
		print 'Exiting...'
		return True


	# Database navigation commands:

	def rel_to_absolute(self, relpath):
		"""Convert relative path names to absolute."""

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

	def do_cd(self, newpathstr):
		"""Change directory."""

		# Normalise group name:
		newpathstr = newpathstr.rstrip('/') + '/'

		# Convert relative paths to absolute:
		newpathstr = self.rel_to_absolute(newpathstr)

		# Check that newpathstr refers to an extant group:
		if f.get(newpathstr, getclass=True) != h5.Group:
			print self.colour.ERROR + "*** Path '{0}' is not a group.".format(newpathstr) \
				+ self.colour.END
		else:
			self.pathstr = newpathstr
			self.set_prompt()

	def do_ls(self, lspath):
		"""List group contents."""

		# Convert relative paths to absolute:
		lspath = self.rel_to_absolute(lspath)

		# Split path and name of object:
		grpPath, grpName = lspath.rsplit('/',1)

		# Normalise group name:
		grpPath = grpPath.rstrip('/') + '/'

		# Error if group path invalid:
		if not isinstance(self.f[grpPath], h5.Group):
			print self.colour.ERROR + 'Invalid path: %s' % (grpPath) + self.colour.END
			return

		list_objects(self.f[grpPath], grpName, self.colour)


	# Command completion:
	
	def path_completion(self, line):
		"""Generic path name completion."""
		
		# Convert relative paths to absolute:
		line = self.rel_to_absolute(line)

		# Split path and (possibly incomplete) group name:
		grpPath, grpName = line.rsplit('/',1)

		# Normalise group name:
		grpPath = grpPath.rstrip('/') + '/'

		# Return if no group at chosen path:
		if not isinstance(self.f[grpPath], h5.Group):
			return []

		result = []

		for key in self.f[grpPath]:

			if not isinstance(self.f[grpPath][key], h5.Group):
				continue

			if key.startswith(grpName):
				result.append(key)

		return result
	
	def complete_cd(self, text, line, begidx, endidx):
		return self.path_completion(line[3:])

	def complete_ls(self, text, line, begidx, endidx):
		return self.path_completion(line[3:])


	# Inline help methods:

	def do_help(self, arg):

		if arg == '':
			print """Shell Commands (help <topic> for more info):
============================================
ls	[path]	List contents of group.
cd	[group]	Change current group.
!	<cmd>	Execute command in system shell.

quit / ^D 	Exits h5shell.
============================================

Type 'license' for distribution and warranty conditions.
"""
		else:
			switch = {
					'ls': self.help_ls,
					'cd': self.help_cd,
					'!': self.help_shell,
					'quit': self.help_quit,
					}
			if arg in switch.keys():
				switch.get(arg)()
			else:
				print self.colour.ERROR + "*** No help on '{0}'.\n".format(arg) \
					+ self.colour.END

	def help_ls (self):
		print """Usage: ls [path]

Lists contents of current group or specified [path].  Wildcards are
accepted.  For example, "ls /foo*" will list all objects whose names
match with the prefix "pref" in the root group.  Similarly, "ls ?bar"
will list all objects in the current group whose names are 4
characters long and end with "bar".

The output of ls describes a single object per line.  Each line uses
formatting conventions determined by the type of database object being
displayed on that line.

* Names of group objects are displayed with a trailing /:
	{1}group_name/{0}

* Names of named datatypes are displayed with a leading +:
	{2}+datatype_name{0}

* Group attributes are displayed with a leading @ and with
  their associated value (or shape if non-scalar) and datatype:
	{3}@attr_name ---------{5} =VALUE (DTYPE){0}

* Datasets are displayed with their multi-dimensional array
  shape and their associated datatype:
	{4}dataset_name -------{5} SHAPE  (DTYPE){0}
""".format(self.colour.END,
		self.colour.GROUP,
		self.colour.DATATYPE,
		self.colour.ATTR,
		self.colour.DATASET,
		self.colour.STATS)

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

	def do_license (self, arg):
		print """h5shell is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

h5shell is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program in the file named COPYING.  If not, see
<http://www.gnu.org/licenses/>.
"""


### MAIN ###
if __name__ == '__main__':

	# Parse command line:
	parser = ArgumentParser(description="Simple shell interface for HDF5 data files.",
						version=__version__)
	parser.add_argument('h5fname', metavar='datafile',
					help="Location of HDF5 formatted data file.")
	parser.add_argument('--no-colour', '--no-color', action='store_true',
					help="Prevent h5shell from using ANSI colour codes.")

	args=parser.parse_args()
	
	print args
	exit(0)

	# Inform about the creation of a new file:
	if not path.exists(args.h5fname):
		print "Error: File '%s' does not exist. Aborting.\n" % (args.h5fname)
		exit(1)

	# Open h5 file:
	try:
		f = h5.File(args.h5fname)
	except IOError:
		print "Error opening HDF5 file '%s'. Aborting." % (args.h5fname)
		print "(Do you have write access to this location?)"
		exit(1)
	
	# Select colour scheme
	colour = Colour(args.no_colour)

	# Start command loop:
	c = H5Cmd(f, args.h5fname, colour)
	c.cmdloop()

	# Close h5 file:
	f.close()