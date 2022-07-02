#!/usr/bin/env python

from argparse import ArgumentParser
from glob import glob
import re

parser = ArgumentParser()
parser.add_argument('args', nargs='*', help='Positional arguments')
parser.add_argument('-t', '--tag', help='Tag to tag image with')
args, passthrough = parser.parse_known_args()

from os import getcwd
from os.path import basename, exists, isdir, isfile
from subprocess import check_call as run

files = [arg for arg in args.args if isfile(arg) and exists(arg)]
dirs = [arg for arg in args.args if isdir(arg) and exists(arg)]

if files:
    if len(files) == 1:
        [dockerfile] = files
    else:
        raise ValueError(f'Found {len(files)} files: {files}')
else:
    dockerfile = 'Dockerfile'
    if not exists(dockerfile):
        dockerfiles = list(glob('*.dockerfile'))
        if len(dockerfiles) == 1:
            [dockerfile] = dockerfiles
        else:
            raise RuntimeError(f"Couldn't find Dockerfile or single *.dockerfile ({dockerfiles})")


if dirs:
    if len(dirs) == 1:
        [context] = dirs
    else:
        raise ValueError(f'Found multiple dirs: {dirs}')
else:
    context = '.'

if args.tag:
    tag = args.tag
else:
    m = re.fullmatch(r'(?P<name>.*)\.dockerfile', basename(dockerfile))
    if m:
        tag = m['name']
    else:
        tag = basename(getcwd())
        pieces = dockerfile.rsplit('.', 1)
        if len(pieces) > 1:
            tag = f'{tag}_{pieces[1]}'

cmd = ['docker', 'build', '-f', dockerfile, '-t', tag] + passthrough + [context]
print(f'Running: {cmd}')
run(cmd)
