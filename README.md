h5shell
=======

A limited command shell interface to HDF5 files (http://www.hdfgroup.org/).
Currently only supports read-only operations, but will include copy, move and
delete operations on database objects.

Software Requirements
---------------------

* A Python 2.x installation (works in 2.6)
* The awesome h5py module - install via pip or download from
  directly http://code.google.com/p/h5py/.
* GNU readline if you want any of the nice path completion. (You do!)

Installation
-----

Ensure the python script is marked as executable and is somewhere in your
execution path. :)

Usage
-----

Run the script with the name of the hdf5 file as its argument to start the
shell.  The inline help system should tell you everything else you need to
know.  Have fun!
