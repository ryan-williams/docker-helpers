#!/usr/bin/env python

import re
from glob import glob
from os import getcwd
from os.path import basename, exists
from subprocess import check_call as run
from sys import stderr

from click import UNPROCESSED, argument, command, option


def err(msg):
    stderr.write(f'{msg}\n')


@command(context_settings=dict(ignore_unknown_options=True))
@option('-a', '--build-arg', 'build_args', multiple=True, help='Build arguments')
@option('-d', '--build-dir', help='Build "context" directory')
@option('-f', '--dockerfile', help='Dockerfile path')
@option('-s', '--silent', is_flag=True, help='Suppress build logs')
@option('-t', '--tag', help='Image tag')
@argument('args', nargs=-1, type=UNPROCESSED)
def main(build_args, build_dir, dockerfile, silent, tag, args):
    if not dockerfile:
        if args:
            *args, dockerfile = args
        else:
            if exists('Dockerfile'):
                dockerfile = 'Dockerfile'
            else:
                dockerfiles = list(glob('*.dockerfile'))
                if len(dockerfiles) == 1:
                    [dockerfile] = dockerfiles
                else:
                    raise RuntimeError(f"Couldn't find Dockerfile or single *.dockerfile ({dockerfiles})")

    if ':' in dockerfile:
        dockerfile0 = dockerfile
        tag0 = tag
        dockerfile, tag = dockerfile.split(':', 1)
        if tag0 and tag0 != tag:
            raise ValueError(f"-t/--tag {tag0} doesn't match tag from {dockerfile0}")
        tag = f"{dockerfile}:{tag}"
    if dockerfile != 'Dockerfile' and not dockerfile.endswith('.dockerfile'):
        dockerfile = f'{dockerfile}.dockerfile'

    if not exists(dockerfile):
        raise FileNotFoundError(f"Couldn't find {dockerfile}")

    if not tag:
        m = re.fullmatch(r'(?P<name>.*)\.dockerfile', basename(dockerfile))
        if m:
            tag = m['name']
        else:
            tag = basename(getcwd())
            pieces = dockerfile.rsplit('.', 1)
            if len(pieces) > 1:
                tag = f'{tag}_{pieces[1]}'

    build_dir = build_dir or '.'
    cmd = [
        'docker', 'build',
        '-f', dockerfile,
        '-t', tag,
        *([] if silent else ['--progress=plain']),
        *[
            arg
            for build_arg in build_args
            for arg in ['--build-arg', build_arg]
        ],
        *args,
        build_dir,
    ]
    err(f'Running: {cmd}')
    run(cmd)


if __name__ == '__main__':
    main()
