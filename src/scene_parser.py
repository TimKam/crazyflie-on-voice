from src.path import *
from yaml import load, dump

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


def parse(path):
    file = open(path, 'r').read()
    yaml_scene = load(file, Loader=Loader)
    room = yaml_scene[0]
    room_measers = room[list(room.keys())[0]][0]
    objects = []
    for object in yaml_scene[1:]:
        measures = object[list(object.keys())[0]][0]
        coordinates = object[list(object.keys())[0]][1]
        objects.append(Translate(Scale(Cube(), *measures), *coordinates))

    return Scene(*room_measers, 0.1, objects)

# parse('../examples/room_spec_1.yaml')





