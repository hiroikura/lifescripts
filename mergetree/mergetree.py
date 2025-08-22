#!/usr/bin/python3
#
# mergetree  - merge two directory trees into one
#
# usage:
#  mergetree [-options] lower-tree upper-tree
#
# options:
#
PROG='mergetree'
DESCRIPTION='merge two directory trees into one'

import sys
import os
import stat

#
# Parse command line arguments
#
import argparse
argparser = argparse.ArgumentParser(prog=PROG, description=DESCRIPTION)
argparser.add_argument('-N', '--dryrun', help='do nothing, just report what to do', action='store_true')
argparser.add_argument('-R', '--remove', help='remove upper tree after merge', action='store_true')
argparser.add_argument('-s', '--strict', help='compare with strict matching', action='store_true')
argparser.add_argument('-B', '--backup', help='backup filename suffix', default='###')
argparser.add_argument('-v', '--verbose', help='verbosly reporting', action='store_true')
argparser.add_argument('-P', '--progress', help='progress reporting', action='store_true')
argparser.add_argument('-S', '--summary', help='reports summary', action='store_true')
argparser.add_argument('lower', help='lower tree (remains)')
argparser.add_argument('upper', help='upper tree (removed)')

args = argparser.parse_args()
#XXX#
#args.dryrun = True
#args.verbose = True

#
# Pretyprinter
#
def verbose(*a):
    if args.verbose:    
        print(' '.join(a))

def internal_error(*a):
    print(' '.join(a), file=sys.stderr)

class ProgressReporter:
    def __init__(self, active=True):
        self.count = 0
        self.mask = 0
        self.heading = None
        self.active = active

    def start(self, heading):
        if not self.active: return    
        self.count = 0
        self.mask = 0
        self.heading = heading
        print(self.heading, end='\r', file=sys.stderr)

    def increment(self):
        if not self.active: return
        self.count += 1
        if (self.count & self.mask) == 0:
            print(self.heading, self.count, end='\r', file=sys.stderr)
        if self.count >= self.mask and self.mask < 1024:
            self.mask = (self.mask << 1) | 1

    def fin(self):
        if not self.active: return
        print(self.heading, self.count, file=sys.stderr)

progress = ProgressReporter(args.progress)

class Summary:
    def __init__(self):
        self.identical = 0
        self.overrided = 0
        self.backupd = 0
        self.special = 0
        self.onlylower = 0
        self.onlyupper = 0
        self.olderfiles = 0
        self.newerfiles = 0
        self.samefiles = 0

        self.moved = 0    
        self.removed = 0
        self.dirremoved = 0

    def only_in_lower(self, f):
        verbose('>>>', f.subpath())
        self.onlylower += 1

    def only_in_upper(self, f):
        verbose('<<<', f.subpath())
        self.onlyupper += 1

    def lower_is_dir(self, f):
        verbose('/**', f.subpath())
        self.backupd += 1

    def upper_is_dir(self, f):
        verbose('**/', f.subpath())
        self.backupd += 1

    def not_file(self, f):
        verbose('---', f.subpath())
        self.special += 1

    def same_inode(self, f):
        verbose('===', f.subpath())
        self.identical += 1

    def older(self, f):
        verbose('>!!', f.subpath())
        self.olderfiles += 1

    def newer(self, f):
        verbose('!!<', f.subpath())
        self.newerfiles += 1

    def samefile(self, f):
        verbose('=*=', f.subpath())
        self.samefiles += 1

    def mismatch(self, f):
        verbose('!!!', f.subpath())
        self.backupd += 1

    def move(self): self.moved += 1
    def remove(self): self.removed += 1
    def removedir(self): self.dirremoved += 1

    def report(self, file=sys.stderr):
        print('', file=file)
        print('Processing Summary:', file=file)
        print(' Moved:', self.moved, file=file)
        print(' Removed files:', self.removed, file=file)
        print(' Removed directories:', self.dirremoved, file=file)
        print('', file=file)
        print(' Identical files:', self.identical, file=file)
        print(' Overridden files:', self.overrided, file=file)
        print(' Backing-upd files:', self.backupd, file=file)
        print(' Special files:', self.special, file=file)
        print(' Only in lower-tree:', self.onlylower, file=file)
        print(' Only in upper-tree:', self.onlyupper, file=file)
        print(' Older files:', self.olderfiles, file=file)
        print(' Newer files:', self.newerfiles, file=file)
        print(' Seems same content:', self.samefiles, file=file)

summary = Summary()        

#
# Elemental class: FileItem
#
class FileItem:
    # base: tree top
    # dir: with heading PATHSEP
    # name: directory entry name

    def subpath(self):
        return self.dir + os.sep + self.name

    def path(self, base=None):
        if not base: base = self.base
        return base + self.subpath()

    def __init__(self, base, dir, name):
        self.base = base
        self.dir = dir
        self.name = name
        self.stat = os.lstat(self.path())
        self.subtree = None

    def __str__(self):
        return self.path()

    def add_subtree(self, tree):
        self.subtree = tree

    def is_dir(self):
        return stat.S_ISDIR(self.stat.st_mode)
    def is_reg(self):
        return stat.S_ISREG(self.stat.st_mode)

    def dev(self):
        return self.stat.st_dev
    def ino(self):
        return self.stat.st_ino
    def mtime(self):
        return self.stat.st_mtime
    def size(self):
        return self.stat.st_size

    def is_sameinode(self, o):
        return self.dev() == o.dev() and self.ino() == o.ino()

#
# Elemental class: DirectoryTree
#
class Tree:
    def _traverse(self, d):
        l = os.listdir(self.base + d)
        l.sort()
        for e in l:
            progress.increment()                
            f = FileItem(self.base, d, e)
            self.entries.append(f)
            if f.is_dir(): # dig into subdirectory
                f.add_subtree(Tree(self.base, d + os.sep + e))

    def __init__(self, base, subdir=''):
        self.base = base
        self.entries = []
        self._traverse(subdir)

    def _dump(self, indent=0, file=sys.stdout):
        for f in self.entries:
            name = f.name
            if f.is_dir():    name += os.sep
            print(' ' * indent, name, sep='', file=file)
            if f.is_dir():
                f.subtree._dump(indent=indent+1, file=file)


    def dump(self, header=None):
        if header: print(header)
        self._dump()

    def __len__(self): return len(self.entries)
    def __getitem__(self, i): return self.entries[i]

#
# Action wrapper
#
def shellcommand(*a):
    cmd = ' '.join(a)    
    if args.dryrun:
        print(cmd)
    else:
        try:
            cl = list(a)
            cmd = cl.pop(0)
            if cmd == 'mv':
                os.rename(cl[0], cl[1])
            elif cmd == 'rm':
                os.remove(cl[0])
            elif cmd == 'rmdir':
                os.rmdir(cl[0])
            else:
                internal_error('unknown shell command:', cmd)
        except OSError as e:
            print('Error in', cmd, ':', e, file=sys.stderr)

#
# file operator
#
def move(f, t, s=''):
    f = str(f)
    t = str(t) + s
    shellcommand('mv', f, t)
    summary.move()

def remove(f):
    f = str(f)
    shellcommand('rm', f)
    summary.remove()

def removedir(d):
    d = str(d)
    shellcommand('rmdir', d)
    summary.removedir()

#
# Comparator
#
def compare(a, b):
    #verbose('***', a.subpath())
    if a.is_dir():
        if b.is_dir():
            compare_tree(a.subtree, b.subtree)
            if args.remove:
                removedir(b)
        else: # lower=directory, upper=file # move upper with renaming
            summary.lower_is_dir(a)
            move(b, a, args.backup)
            pass
    else:
        if b.is_dir(): # lower=file, upper=directory # move upper with renaming
            summary.upper_is_dir(b)
            move(b, a, args.backup)
            pass
        else: # lower,upper=file # compare it
            if not a.is_reg() or not b.is_reg():
                # not reguler file, remove upper and just skip
                summary.not_file(a)
                remove(b)
            elif a.is_sameinode(b):   # same file
                summary.same_inode(a)
                remove(b)
            elif (a.mtime() > b.mtime()):  # lower is newer than upper, remove upper
                summary.older(b)
                remove(b)   #TBD# backup?
            elif (a.mtime() < b.mtime()):  # lower is older than upper, remove lower and move upper
                summary.newer(b)
                remove(a)   #TBD# backup?
                move(b, a)
            else: # lower and upper have same mtime, remove upper?
                if a.size() == b.size(): # same size, may be identical file
                    summary.samefile(a)
                    if args.strict:
                        pass #TBD# byte-by-byte compare
                    else:
                        remove(b)
                else:
                    summary.mismatch(a)
                    move(b, a, args.backup)

def only_in_lower(f):
    summary.only_in_lower(f)
    # file in lower tree is remaining, just skip it

def only_in_upper(f, lb):
    summary.only_in_upper(f)
    # move upper file to lower directory
    move(f.path(), f.path(lb))

def compare_tree(tree_a, tree_b):
    ia = 0
    ib = 0
    while ia < len(tree_a) and ib < len(tree_b):
        a = tree_a[ia]
        b = tree_b[ib]
        if a.name < b.name:
            only_in_lower(a)
            ia += 1
        elif b.name < a.name:
            only_in_upper(b, tree_a.base)
            ib += 1
        else:
            compare(a, b)
            ia += 1
            ib += 1
    for i in range(ia, len(tree_a)):
        only_in_lower(tree_a[i])
    for i in range(ib, len(tree_b)):
        only_in_upper(tree_b[i], tree_a.base)

#
# Program main
#

progress.start('Listing files:' + args.lower + ':')
tree_lower = Tree(args.lower)
progress.fin()

progress.start('Listing files:' + args.upper + ':')
tree_upper = Tree(args.upper)
progress.fin()

#tree_lower.dump(header='Lower Tree:')
#tree_upper.dump(header='Upper Tree:')

compare_tree(tree_lower, tree_upper)

if args.summary:
    summary.report()
