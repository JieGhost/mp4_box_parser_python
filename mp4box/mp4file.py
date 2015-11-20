__author__ = 'yujiechen'

from util import ParseBox
from box import BoxDict, Box


def FindBox(btype, root):
    ret = []
    if hasattr(root, 'boxes'):
        for child in root.boxes:
            if child.boxtype == btype:
                ret.append(child)
            else:
                ret.extend(FindBox(btype, child))

    return ret


class MP4File(object):
    def __init__(self, f, filesize):
        self.filesize = filesize
        self._bcount = 0
        self.boxes = []

        while self._bcount < self.filesize:
            tempbox = ParseBox(f, BoxDict, Box)
            self.boxes.append(tempbox)
            self._bcount += tempbox.boxsize

