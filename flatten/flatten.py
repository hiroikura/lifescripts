#!/usr/bin/python3
#
# flatten
#
# usage: flatten [options] path...
#
# options:
#  -l --level N
#  -s --separator STR
#

import sys
import os

#
# Parse command line arguments
#
import argparse
PROG_NAME='flatten'
PROG_DESCRIPTION='flatten pathname'
argparser = argparse.ArgumentParser(prog=PROG_NAME, description=PROG_DESCRIPTION)
argparser.add_argument('-l', '--level', help='flatten level', type=int, default=1)
argparser.add_argument('-s', '--separator', help='path seperator string', default='-')
argparser.add_argument('-w', '--remove-whitespaces', help='remove white space characters from pathname', action='store_true')
argparser.add_argument('-N', '--dryrun', help='do nothing, just scanning', action='store_true')
argparser.add_argument('path', nargs='+', help='path to flatten')

args = argparser.parse_args()

# some preparation
if args.remove_whitespaces:
    WHITE_SPACES = [' ', '\t', '\n', '\r']
    m = {}
    for c in WHITE_SPACES:
        m[c] = None
    whitespace_pattern = str.maketrans(m)

# process one file
def do_process(src, dst):
    if args.remove_whitespaces:
        dst = dst.translate(whitespace_pattern)    
    if args.dryrun:
        print('mv %s %s'%(src,dst))
    else:
        os.rename(src, dst)

#
# Traverse directory tree
#
for p in args.path:
    for path, dirs, files in os.walk(p):
        if len(path.split(sep=os.sep)) > args.level:
            continue
        for file in files:
            src = os.path.join(path, file)
            dst = path + args.separator + file
            do_process(src, dst)
