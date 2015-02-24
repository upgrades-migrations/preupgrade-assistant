#!/usr/bin/python2
from __future__ import print_function

import re
import sys
import os


# test whether given file list contains .ini file = is leaf
def contains_ini_file(files):
    return filter(lambda x: len(x) > 5 and x.endswith('.ini'), files)

# set tested directory 
if (len(sys.argv) == 1):
    # either use input directory
    directory = "./"
else:
    # or use ./ if there is no input directory
    directory = sys.argv[1]
    print ("check ", sys.argv[1], " directory")


# ----------------------------------------------------------------
# test - there is no XCCDF variable in postupgrade.d content files
#-----------------------------------------------------------------
# test content files for "$XCCDF" string

def find_xccdf_return_code():
    for root, dirs, files in os.walk("./"):
        # look for "postupgrade.d" subdirectory
        if "postupgrade.d" in dirs:

            # find all files in this directory
            pu_path = os.path.join(root, "postupgrade.d")
            for f in os.listdir(pu_path):
                # find all files
                pu_file_path = os.path.join(pu_path, f)
                if os.path.isfile(pu_file_path):
                    # test them for $XCCDF string
                    pu_file = open(pu_file_path, "r")
                    for line in pu_file:
                        if re.search("\$XCCDF", line):
                            print ("Error: file ", pu_file_path, " contains ", line)


def find_two_same_contents():
    # ----------------------------------------------------------
    # test -  there are not two content files with the same name
    #-----------------------------------------------------------
    for root, dirs, files in os.walk("./"):

        # look for leaf directory
        if contains_ini_file(files):

            for file_name in files:
                if ((file_name != "solution.txt") and (file_name != "group.xml") and (file_name != "READY")):
                    # for all files except of solution.txt and
                    # group.xml have to have unique filenames
                    # test whether file name is unique

                    for root2, dirs2, files2 in os.walk("./"):
                        if ((root != root2) and (contains_ini_file(files2) == 1) and (file_name in files2)):
                                print ("Error: file ", file_name, "in two subdirs ",
                                       root, " and ", root2)

#