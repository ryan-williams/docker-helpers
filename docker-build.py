#!/usr/bin/env python

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument('args',nargs='*',help='Positional arguments')
parser.add_argument('-t','--tag',help='Tag to tag image with')
args, passthrough = parser.parse_known_args()

from subprocess import check_call as run

from pathlib import Path

files = [ arg for arg in args.args if Path(arg).is_file ]
dirs = [ arg for arg in args.args if Path(arg).is_dir ]

if files:
    if len(files) == 1:
        [dockerfile] = files
    else:
        raise ValueError(f'Found multiple files: {files}')
else:
    dockerfile = 'Dockerfile'

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
    tag = Path.cwd().name
    pieces = dockerfile.rsplit('.',1)
    if len(pieces) > 1:
       tag = f'{tag}_{pieces[1]}'

cmd = [ 'docker','build','-f',dockerfile,'-t',tag ] + passthrough + [ context ]
print(f'Running: {cmd}')
run(cmd)
