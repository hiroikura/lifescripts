#!/usr/bin/python3
#
# rerename  - rename by regex
#
# usage:
#  rerename [-options] regex subto files...
#
# options:
#  -r  --recursive
#  -N  --dryrun
PROG = 'rerename'
DESCRIPTION = 'rename files by reguler expression'

import sys
import os
import re

#
# Parse command line arguments
#
import argparse
argparser = argparse.ArgumentParser(prog=PROG, description=DESCRIPTION)
argparser.add_argument('-r', '--recursive', help='scan recursively', action='store_true')
argparser.add_argument('-N', '--dryrun', help='do nothing, just report what to do', action='store_true')
argparser.add_argument('regex', help='reguler expression to match')
argparser.add_argument('subto', help='substitute to')
argparser.add_argument('path', nargs='+', help='path to rename')

args = argparser.parse_args()

#
# Application main
#

### TBD: recursive

# obtain regex and compile
regex = re.compile(args.regex)
subto = args.subto

# process for one file
def do_process(src):
    if (not (os.path.isfile(src) or os.path.isdir(src))):
        return None

    #if (not regex.match(p)):
    #    return None

    dst = regex.sub(subto, p)
    if dst == src: return
    if args.dryrun:
        print('rename %s to %s'%(src,dst))
    else:
        os.rename(src, dst)    

# scan paths
for p in args.path:
    do_process(p)
