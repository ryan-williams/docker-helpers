#!/usr/bin/env python
import shlex
from functools import partial
from os import getcwd
from os.path import basename
from re import fullmatch
from subprocess import check_output, Popen, check_call

from click import argument, command, echo, option, UNPROCESSED


err = partial(echo, err=True)


@command(context_settings=dict(ignore_unknown_options=True))
@option('-E', '--env-file', 'env_files', multiple=True, help='Environment files')
@option('-I', '--non-interactive', is_flag=True, help='Non-interactive mode (disable passing `-it`)')
@option('-k', '--keep', is_flag=True, help='Keep container after it exits (disable passing `--rm`)')
@option('-n', '--name', help='Container name')
@option('-p', '--port', 'ports', multiple=True, help='Port mappings')
@option('-v', '--volume', 'volumes', multiple=True, help='Volume mappings; relative paths supported')
@argument('args', nargs=-1, type=UNPROCESSED)
def main(env_files, non_interactive, keep, name, ports, volumes, args):
    """`docker run` wrapper with some defaults and conveniences.

    By default:
    - interactive (`-it`)
    - remove container after it exits (`--rm`)
    - run the most recently built tagged image (if no positional args are provided)
    - second positional arg (after image) is used as `--entrypoint`
    - use image name as the container name
    - speculatively remove existing container with the same name

    Additional conveniences:
    - port mappings can be integers (e.g. `8080` → `8080:8080`)
    - `-E` alias for `--env-file`
    """
    opt_args = []
    while args and args[0].startswith('-'):
        k, v, *args = args
        opt_args += [ k, v ]

    err(f"{args=}, {opt_args=}")
    img = None
    if args:
        img, *args = args

    entrypoint = None
    if args:
        entrypoint, *args = args

    if not img:
        cmd = [ 'docker', 'image', 'ls', '--format', '{{.Repository}}:{{.Tag}}', '*:*', ]
        err(f"Running: {shlex.join(cmd)}")
        img = check_output(cmd).decode().splitlines()[0].rstrip('\n')
        err(f'Found latest image: {img}')

    if not name:
        name = img.split(':')[0]
        err(f'Using container name: {name}')

    cmd = ['docker', 'container', 'rm', name]
    err(f"Running: {shlex.join(cmd)}")
    Popen(cmd).wait()

    cmd = ['docker', 'run', '--name', name]
    if not non_interactive:
        cmd += ['-it']
    if not keep:
        cmd += ['--rm']

    cmd += opt_args
    if entrypoint:
        cmd += [ '--entrypoint', entrypoint ]

    for env_file in env_files:
        cmd += ['-env-file', env_file]

    for volume in volumes:
        pcs = volume.split(':')
        if len(pcs) != 2:
            raise ValueError(f'Invalid volume mapping: {volume}')
        src, dst = pcs
        if src[0] != '/':
            src = f'{getcwd()}/{src}'
        if dst[-1] == "/":
            dst += basename(src)
        cmd += ['-v', f'{src}:{dst}']

    for port in ports:
        if fullmatch(r'\d+', port):
            port = f'{port}:{port}'
        cmd += ['-p', port]

    cmd += [img, *args]
    err(f"Running: {shlex.join(cmd)}")
    check_call(cmd)


if __name__ == '__main__':
    main()
