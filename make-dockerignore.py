#!/usr/bin/env python
#
# Make a .dockerignore file that only accepts files currently tracked by Git
#
# See https://j.mp/make-dockerignore

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument('-G','--no-git-dir',action='store_true',help="When set, don't un-ignore the .git directory (i.e. ignore it)")
parser.add_argument('-d','--description',action='count',default=0,help="How verbose of a comment/header message to write")
parser.add_argument('-D','--no-description',action='store_true',help="When set, don't output any header message")
args = parser.parse_args()

no_git_dir = args.no_git_dir

if args.no_description:
  description = 0
else:
  description = args.description
  if description == 0:
        description = 1

from pathlib import Path
import shlex
from subprocess import check_output as run
import sys

with open('.dockerignore','w') as f:
  cmd = shlex.join([Path(sys.argv[0]).name] + sys.argv[1:])
  url = 'https://j.mp/make-dockerignore'
  if description == 1:
    f.write('# Generated by `%s`; see %s\n' % (cmd, url))
  elif description >= 2:
    f.write('# Exclude all files except those tracked by Git.\n')
    f.write('#\n')
    f.write('# Generated by:\n')
    f.write('#\n')
    f.write('# \t%s\n' % cmd)
    f.write('#\n')
    f.write('# See %s\n' % url)
    f.write('*\n')

  if not no_git_dir:
    f.write('!.git\n')

  f.flush()

  [
    f.write(f'!{line}\n')
    for line in
    run(['git','ls-files']).decode().split('\n')
    if line
  ]