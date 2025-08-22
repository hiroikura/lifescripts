#!/usr/bin/python3
#
# hdupes  - identify duplicate files
#

import sys
import os
from stat import *
import hashlib

#
# program constants
#
HASHGEN = hashlib.sha1
BUFSIZE = 4096

#
# class: FileNode
#
# keyed by:
#  (dev, ino)
#  filesize
#  hash1 (first Nbytes)
#  
#
class FileNode:
    def __init__(self, path, stat=None):
        self._path = path
        self._linked = [] # list of str
        self._stat = os.lstat(path) if stat is None else stat

    def fileno(self):
        return (self._stat.st_dev, self._stat.st_ino)

    def link(self, path):
        self._linked.append(path)

    def path(self):
        return self._path

    def size(self):
        return self._stat.st_size

class FileStore:
    def __init__(self):
        self._store = {} # dictionary keyed by (dev,ino)

    def add(self, path, stat=None):
        if stat is None:
            stat = os.lstat(path)
        fileno = (stat.st_dev, stat.st_ino)
        if fileno in self._store:
            self._store[fileno].link(path)
            return None
        else:
            fn = FileNode(path, stat)
            self._store[fileno] = fn
            return fn

    def nodes(self):
        return self._store.values()
    
    def add_file(self, path, stat=None):
        if stat is None:
            stat = os.lstat(path)
        if not S_ISREG(stat.st_mode):
            return

        fn = self.add(path, stat)
        if fn is None:
            return  # already linked, skip it
 
    def scan_directory(self, path):
        for base, dirs, files in os.walk(path):
            for file in files:
                self.add_file(os.path.join(base, file))


filestore = FileStore()            

#
# pretty printers
#


#
# command line
#
PROG = "hdupes"
DESCRIPTION = "identify duplicate files"
import argparse
argparser = argparse.ArgumentParser(prog=PROG, description=DESCRIPTION)
#argparser.add_argument('-l', '--hardlink', help='alternate duplicates by hard-link', action='store_true')
#argparser.add_argument('-d', '--delete', help='delete duplicate files', action='store_true')
#argparser.add_argument('-S', '--scanonly', help='dont stat for files, just scanning', action='store_true')
argparser.add_argument('-r', '--recurse', help='for every directory given follow subdirectories encounterd within', action='store_true')
argparser.add_argument('-N', '--dryrun', help='dont (re)move files, just reporting', action='store_true')
argparser.add_argument('-P', '--progress', help='show progress reporting', action='store_true')
argparser.add_argument('files', nargs='+', help='fdupes outputs')
args = argparser.parse_args()

#
# File Digest calculator
#
class FileDigest:
    LEVELSCALER = 8 # log2

    def xxdbg(self):
        print('HASHGEN=', HASHGEN)
        print('BUFSIZE=', BUFSIZE)
        print('LEVELSCALER=', self.LEVELSCALER)

    def calc(self, path, level=0):
        with open(path, 'rb') as f:
            m = HASHGEN()
            for i in range(1 << level):
                buf = f.read(BUFSIZE)
                if len(buf) == 0: break
                m.update(buf)
        return m.digest()


#
# experimental main
#
class HashTable:
    def __init__(self, level=0):
        # prepare level0 dictionary
        self._table = dict()
        self._level = level

    def append(self, key, value):
        if key in self._table:
            e = self._table[key]
            if isinstance(e, list):
                e.append(value)
            else:
                self._table[key] = [e, value]
        else:
            self._table[key] = value

    def dump(self, file=sys.stdout):
        for key, value in self._table.items():
            if isinstance(value, list):
                p = [fn.path() for fn in value]
            else:
                p = value.path()
            print(key.hex(), p, file=file)

def error(*args):
    print(*args, file=sys.stderr)

def compare_file_content(file1, file2, offset=0):
    bufsize = BUFSIZE
    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
        if offset > 0:
            d1.seek(offset)
            d2.seek(offset)
        while True:
            d1 = f1.read(bufsize)
            d2 = f2.read(bufsize)
            if d1 != d2:
                return False
            if len(d1) == 0:
                break
    return True

def process_file(path, stat=None):
    pass

#
# Phase 1:
#  make 'filestore' with scanning all directory
#  generated: pure list of files which has no hard-linked duplicates
#
for path in args.files:
    try:
        if not os.path.exists(path):
            error(path, 'not found')
            continue
        s = os.lstat(path)
    except OSError as e:
        error(str(e))

    m = s.st_mode
    if S_ISDIR(m):
        if args.recurse:
            filestore.scan_directory(path)
        else:
            error(path, 'is directory, skipping')
    elif S_ISREG(path):
        filestore.add(path, s)
    else:
        error(path, 'is not a reguler file, skipping')

files = filestore.nodes()
#xxx#del filestore

#
# Phase 2: for each digest level
#  2.1: calculate digest for each file
#  2.2: eliminate entries which has same digest
#
hashlevel = 0
hashtable = HashTable(hashlevel)

digester = FileDigest()

for fn in files:
    try:
        v = digester.calc(fn.path(), hashlevel)
        hashtable.append(v, fn)
    except OSError as e:
        error(str(e))
hashtable.dump()

# XXX
# debug dump
#
