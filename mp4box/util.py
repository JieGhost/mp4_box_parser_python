__author__ = 'yujiechen'

import struct


class ParsingError(Exception):
    def __init__(self, boxtype):
        super(ParsingError, self).__init__()
        self.boxtype = boxtype

    def __str__(self):
        return repr(self.boxtype)


def read_value(fin, num_bits, mode='unsigned'):
    """
    :param fin: source file handle
    :param num_bits: number of bits
    :param mode: unsigned / signed / fix_point / char / void
    :return: integer when success, None when fail
    """
    num_bytes = num_bits / 8
    data = fin.read(num_bytes)
    if mode == "char" or mode == "void":
        return data
    elif mode == "fix_point":
        if num_bytes == 2:
            ret = str(struct.unpack('>B', data[0])[0])
            ret += '.' + str(struct.unpack('>B', data[1])[0])
            return ret
        elif num_bytes == 4:
            ret = str(struct.unpack('>H', data[0:2])[0])
            ret += '.' + str(struct.unpack('>H', data[2:])[0])
            return ret
    elif mode == "signed":
        if num_bytes == 1:
            return struct.unpack('>b', data)[0]
        elif num_bytes == 2:
            return struct.unpack('>h', data)[0]
        elif num_bytes == 4:
            return struct.unpack('>i', data)[0]
        else:
            print "unsupported number of bytes for signed"
    else:
        if num_bytes == 1:
            return struct.unpack('>B', data)[0]
        elif num_bytes == 2:
            return struct.unpack('>H', data)[0]
        elif num_bytes == 3:
            three_byte = struct.unpack('>BBB', data)
            return (three_byte[0] << 16) | (three_byte[1] << 8) | three_byte[2]
        elif num_bytes == 4:
            return struct.unpack('>I', data)[0]
        elif num_bytes == 6:
            six_byte = struct.unpack('>BBBBBB', data)
            ret = ((six_byte[0] << 40) |
                   (six_byte[1] << 32) |
                   (six_byte[2] << 24) |
                   (six_byte[3] << 16) |
                   (six_byte[4] << 8) |
                   (six_byte[5]))
            return ret
        elif num_bytes == 8:
            return struct.unpack('>Q', data)[0]
        else:
            print "unsupported number of bytes for unsigned"

    return None


def FindBoxType(f):
    data = f.read(4)
    data = f.read(4)
    f.seek(-8, 1)
    return data


def ParseBox(f, box_dict, default_box):
    btype = FindBoxType(f)
    if btype in box_dict.keys():
        tempbox = box_dict[btype](f)
        return tempbox
    else:
        tempbox = default_box(f)
        tempbox.skipbox(f)
        return tempbox
