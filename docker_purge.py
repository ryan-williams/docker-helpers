#!/usr/bin/env python
#
# usage: python3 docker_descendants.py <image_id> ...

from dataclasses import dataclass
import sys
from subprocess import check_output

def run(cmd):
    return check_output(cmd, universal_newlines=True).splitlines()


def parse_links(lines):
    parseid = lambda s: s.replace('sha256:', '')
    for line in reversed(list(lines)):
        yield list(map(parseid, line.split()))


def docker_links(images):
    cmd = [ 'docker', 'inspect', '--format={{.Id}} {{.Parent}}']
    return run(cmd + images)


def docker_images(*args):
    return run(('docker', 'images') + args)


@dataclass
class Image:
    images = {}
    _initd = False
    _initing = False

    def __new__(cls, id):
        if isinstance(id, Image): return id
        if id not in cls.images:
            if cls._initd:
                images = [ image for image in cls.images.keys() if image.startswith(id) ]
                if len(images) == 1:
                    #print(f'Found image: {id} => {images[0]}')
                    id = images[0]
                    return cls.images[id]
                else:
                    raise KeyError(f'{len(images)} images match {id}')
            elif not cls._initing:
                cls.init()
                return cls.__new__(cls, id)
            self = super(cls, Image).__new__(cls)
            cls.images[id] = self
        return cls.images[id]

    def __init__(self, id):
        if hasattr(self, 'id'): return
        self.id = id
        self.parent = None
        self.children = []
        self.containers = []

    def __dict__(self):
        d = {'id':self.id}
        if self.parent: d['parent'] = self.parent.id
        if self.children: d['children'] = [ i.id for i in self.children ]
        if self.containers: d['containers'] = self.containers
        return d

    def __str__(self):
        return f'Image({",".join([f"{k}={v}" for k,v in self.__dict__().items() ])})'

    def __repr__(self): return str(self)

    def __hash__(self): return hash(self.id)

    @classmethod
    def get(cls, id, default=None): return cls.images.get(id, default)

    @classmethod
    def dict(cls):
        return {
            id: {
                k:v
                for k,v
                in img.__dict__().items()
                if k != 'id'
            }
            for id, img
            in Image.images.items()
        }

    @classmethod
    def reinit(cls):
        cls._initd = False
        cls.init()

    @classmethod
    def init(cls):
        if cls._initd or cls._initing: return
        print(f'Initializing docker images')
        cls._initing = True

        all_images = docker_images('--all', '--quiet')

        for link in parse_links(docker_links(all_images)):
            if len(link) == 1:
                id = link[0]
                parent = None
            elif len(link) == 2:
                [ id, parent ] = link
            else:
                raise ValueError(link)

            image = Image(id)
            if parent:
                parent = Image(parent)
                image.parent = parent
                parent.children.append(image)

        containers = {}
        image_names = []
        for line in run(['docker','container','ls','--all','--format={{.ID}} {{.Image}}']):
            [ container_id, image ] = line.split(' ',1)
            containers[container_id] = image
            if image not in cls.images:
                image_names.append(image)

        image_ids = run(['docker','image','inspect','--format={{.ID}}'] + image_names)
        assert len(image_ids) == len(image_names)
        def rm_prefix(prefix, s):
            if not s.startswith(prefix):
                raise ValueError(f"{s} doesn't start with {prefix}")
            return s[len(prefix):]

        image_ids = [ rm_prefix('sha256:', s) for s in image_ids ]

        image_name_map = {
            name: id
            for name, id in
            zip(image_names, image_ids)
        }

        containers = {
            container_id: image_name_map.get(image, image)
            for container_id, image
            in containers.items()
        }

        for container_id, image_id in containers.items():
            Image(image_id).containers.append(container_id)

        cls._initd = True
        cls._initing = False
        print(f'Initialized {len(cls.images)} images, {len(containers)} containers')


def closure(image, images=None, image_set=None, containers=None):
    images = images or []
    image_set = image_set or set()
    containers = containers or []
    image = Image(image)
    if not image in image_set:
        images.append(image)
        image_set.add(image)

    containers += image.containers
    new_children = set(image.children) - image_set
    image_set.update(new_children)
    images += new_children
    for child in image.children:
        images, containers = closure(child, images, image_set, containers)

    return images, containers


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-n','--dry-run',action='store_true', help="When set, print containers and images to remove, but don't remove them")
    parser.add_argument('-v','--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('image', nargs='+', help='Images to search for descendents of')
    args, extra = parser.parse_known_args()

    for image in args.image:
        Image.reinit()
        if args.verbose:
            import yaml
            print(
                yaml.safe_dump(
                    Image.dict(),
                    sort_keys=False,
                )
            )

        images, containers = closure(image)
        print(
            'Removing %d images:\n\t%s\n\n%d containers:\n\t%s' % (
                len(images),
                "\n\t".join([ image.id for image in images ]),
                len(containers),
                "\n\t".join(containers)
            ))

        if not args.dry_run:
            for container in containers:
                cmd = ['docker','container','rm',container]
                print(f'run: {cmd}')
                run(cmd)

            for image in reversed(images):
                cmd = ['docker','rmi','--no-prune',image.id]
                print(f'run: {cmd}')
                run(cmd)
