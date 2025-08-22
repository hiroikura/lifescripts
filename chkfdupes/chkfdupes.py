#!/usr/bin/python3
#
# chkfdupes
#

import sys

#
# NewLine Separated Value file handler
#
class NslvReader:
    def lineno():
        doc = "current line number"
        def fget(self):  return self.__lineno
        return locals()
    lineno = property(**lineno())

    def __init__(self, file=None):
        self.__file = file
        self.__lineno = 1

    def next(self):
        r = []
        for l in self.__file:
            self.__lineno += 1
            l = l.rstrip()
            if len(l) == 0:
                return r
            r.append(l)
        return r if len(r) > 0 else None

    def __iter__(self):
        return self
    def __next__(self):
        r = self.next()
        if not r:
            raise StopIteration()
        return r

#
# Statistics collector
#
class Stats:
    def __init__(self):
        self.num_entries = 0
        self.num_empty = 0
        self.num_duplicates = 0
        self.max_duplicates = 0
        self.saving_blocks = 0
    def trace(self):
        if args.progress: print(self.num_entries, end='\r')
    def add_entry(self, n=1):
        self.num_entries += n
        self.trace()
    def add_empty(self, n=1):
        self.num_empty += n
    def add_duplicates(self, n=1):
        self.num_duplicates += n
        if n > self.max_duplicates:
            self.max_duplicates = n
    def add_saving_blocks(self, n):
        self.saving_blocks += n

    def report(self, file=sys.stderr):
        print(
'''Total entries: {:,}
Empty records(insane): {:,}
Total duplicate files: {:,}
Max duplication for a file: {}
Total saving bytes: {:,}'''.format(
    self.num_entries,
    self.num_empty,
    self.num_duplicates,
    self.max_duplicates,
    self.saving_blocks * 512), file=file)

stats = Stats()
    
#
# main parser
#
import os

class FileItem:
    def __init__(self, filename, s=None):
        if not s:
            s = os.lstat(filename)
        self.__name = filename
        self.__stat = s
    @property
    def name(self): return self.__name
    @property
    def size(self): return self.__stat.st_size
    @property
    def blocks(self): return self.__stat.st_blocks
    @property
    def dev(self): return self.__stat.st_dev
    @property
    def ino(self): return self.__stat.st_ino
    @property
    def mtime(self): return self.__stat.st_mtime

    def new(filename):
        fi = None    
        try:
            s = os.lstat(filename)
            fi = FileItem(filename, s)
        except OSError as e:
            print(e, file=sys.stderr)
        return fi

#
# file operatoin wrappeer
#
def shell_command(cmd, *a):
    commandline = cmd + ' ' + ' '.join(a)
    if args.dryrun:
        print(commandline)
    else:
        try:
            if cmd == 'rm':
                os.remove(a[0])
            elif cmd == 'ln':
                os.link(a[0], a[1])
        except OSError as e:
            print('%s: %s' % (commandline, str(e)), file=sys.stderr)


def alter_duplicate(orig, dup):
    # remove duplicate
    if args.hardlink or args.delete:
        shell_command('rm', dup.name)    
    # link original
    if args.hardlink:
        shell_command('ln', orig.name, dup.name)

def process_record(r):
    stats.add_entry()
    if len(r) == 0:
        stats.add_empty()
        return

    if args.scanonly:
        stats.add_duplicates(len(r) - 1)
        return

    # stat for each entry (skip file with error)
    ls = []
    for f in r:
        fi = FileItem.new(f)
        if fi:
            ls.append(fi)
    if len(ls) < 2:
        return

    # sort by newer and smaller(allocated)
    ls.sort(key=lambda x: (-x.mtime, x.blocks))

    # loop
    a = ls.pop(0)
    ndups = 0
    for b in ls:
        # some checks
        if a.dev == b.dev and a.ino == b.ino:
            print('%s and %s link to same inode'%(a.name, b.name))
        elif a.size != b.size:
            print('%s and %s have different file size'%(a.name, b.name))
        #elif a.blocks != b.blocks:
        #    print('%s and %s have different allocated blocks'%(a.name, b.name))
        else:
            ndups += 1
            stats.add_saving_blocks(b.blocks)
            alter_duplicate(a, b)
    stats.add_duplicates(ndups)


def parse(f, filename):
    reader = NslvReader(file=f)
    while True:
        try:
            r = reader.next()
        except Exception as e:
            print('%s:%d: %s' % (filename, reader.lineno, str(e)), file=sys.stderr)
        if not r: break

        process_record(r)

#
# parse commandline
#
PROG = "chkfdupes"
DESCRIPTION = "parse output of fdupes command"
import argparse
argparser = argparse.ArgumentParser(prog=PROG, description=DESCRIPTION)
argparser.add_argument('-l', '--hardlink', help='alternate duplicates by hard-link', action='store_true')
argparser.add_argument('-d', '--delete', help='delete duplicate files', action='store_true')
argparser.add_argument('-S', '--scanonly', help='dont stat for files, just scanning', action='store_true')
argparser.add_argument('-N', '--dryrun', help='dont (re)move files, just reporting', action='store_true')
argparser.add_argument('-P', '--progress', help='show progress reporting', action='store_true')
argparser.add_argument('file', nargs='+', help='fdupes outputs')
args = argparser.parse_args()


#
# main routine
#
for filename in args.file:
    if filename == '-':
        parse(sys.stdin, '(stdin)')
    else:
        try:    
            with open(filename) as f:
                parse(f, filename)
        except OSError as e:
            print('%s: %s' % (filename, str(e)), file=sys.stderr)

#
# final report
#
stats.report(file=sys.stderr)
