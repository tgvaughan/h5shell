h5shell
=======

A limited command shell interface to HDF5 files (http://www.hdfgroup.org/).
Currently supported operations include:
* exploring file contents using `cd` and `ls` commands,
* removing database objects using the `rm` command.

Note that removing database objects is fairly pointless at this stage due to a
deficiency in HDF5 which causes the free space by this operation to be "lost"
(i.e. the object is unlinked but space is not reallocated).  The h5repack
utility provided by the HDF group can be used to reclaim this lot space.

The ability to move and copy objects around will be added in future.

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
