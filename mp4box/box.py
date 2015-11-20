# coding=utf-8
from util import *

__author__ = 'yujiechen'

DEFAULT_INDENTATION = 4


class Box(object):
    """
    aligned(8) class Box (unsigned int(32) boxtype,
            optional unsigned int(8)[16] extended_type) {
        unsigned int(32) size;
        unsigned int(32) type = boxtype;
        if (size==1) {
            unsigned int(64) largesize;
        } else if (size==0) {
            // box extends to end of file
        }
        if (boxtype==‘uuid’) {
            unsigned int(8)[16] usertype = extended_type;
        }
    }
    """
    def __init__(self, f):
        self._bytecount = 0
        self.file_offset = f.tell()

        self.boxsize = read_value(f, 32)
        self._bytecount += 4

        self.boxtype = read_value(f, 32, "char")
        self._bytecount += 4

        if self.boxsize == 1:
            self.boxsize = read_value(f, 64)
            self._bytecount += 8
        elif self.boxsize == 0:
            f.seek(0, 2)
            self.boxsize = f.tell() - self.file_offset
            f.seek(self.file_offset, 0)

    def skipbox(self, f):
        f.seek(self.boxsize - self._bytecount, 1)
        self._bytecount = self.boxsize


class FullBox(Box):
    """
    aligned(8) class FullBox(unsigned int(32) boxtype, unsigned int(8) v, bit(24) f)
        extends Box(boxtype) {
        unsigned int(8) version = v;
        bit(24) flags = f;
    }
    """
    def __init__(self, f):
        super(FullBox, self).__init__(f)

        self.version = read_value(f, 8)
        self._bytecount += 1

        self.flag = read_value(f, 24)
        self._bytecount += 3


class ContainerBox(Box):
    def __init__(self, f):
        super(ContainerBox, self).__init__(f)

        self.boxes = []

        while self._bytecount < self.boxsize:
            tempbox = ParseBox(f, BoxDict, Box)
            self.boxes.append(tempbox)
            self._bytecount += tempbox.boxsize


class Co64(FullBox):
    """
    aligned(8) class ChunkLargeOffsetBox
        extends FullBox(‘co64’, version = 0, 0) {
        unsigned int(32) entry_count;
        for (i=1; i <= entry_count; i++) {
            unsigned int(64) chunk_offset;
        }
    }
    """
    def __init__(self, f):
        super(Co64, self).__init__(f)

        self.entry_count = read_value(f, 32)
        self._bytecount += 4

        self.chunk_offset = []
        idx = 1
        while idx <= self.entry_count:
            self.chunk_offset.append(read_value(f, 64))
            self._bytecount += 8
            idx += 1


class Free(Box):
    def __init__(self, f):
        super(Free, self).__init__(f)
        self.skipbox(f)


class Ftyp(Box):
    """
    aligned(8) class FileTypeBox
        extends Box(‘ftyp’) {
        unsigned int(32) major_brand;
        unsigned int(32) minor_version;
        unsigned int(32) compatible_brands[]; // to end of the box
    }
    """
    def __init__(self, f):
        super(Ftyp, self).__init__(f)

        self.major_brand = read_value(f, 32, "char")
        self._bytecount += 4

        self.minor_version = read_value(f, 32)
        self._bytecount += 4

        self.compatible_brands = []
        while self.boxsize - self._bytecount > 0:
            self.compatible_brands.append(read_value(f, 32, "char"))
            self._bytecount += 4


class Hdlr(FullBox):
    """
    aligned(8) class HandlerBox extends FullBox(‘hdlr’, version = 0, 0) {
        unsigned int(32) pre_defined = 0;
        unsigned int(32) handler_type;
        const unsigned int(32)[3] reserved = 0;
        string name;
    }
    """
    def __init__(self, f):
        super(Hdlr, self).__init__(f)

        pre_defined = read_value(f, 32)
        self._bytecount += 4
        if pre_defined != 0:
            raise ParsingError(self.boxtype)

        self.handler_type = read_value(f, 32, "char")
        self._bytecount += 4
        if self.handler_type not in ['vide', 'soun', 'hint', 'meta', 'auxv']:
            raise ParsingError(self.boxtype)

        for idx in xrange(3):
            read_value(f, 32)
        self._bytecount += 12

        data = f.read(self.boxsize - self._bytecount)
        self.name = data[0:-1]
        self._bytecount = self.boxsize


class Mdia(ContainerBox):
    def __init__(self, f):
        super(Mdia, self).__init__(f)


class Minf(ContainerBox):
    def __init__(self, f):
        super(Minf, self).__init__(f)


class Moov(ContainerBox):
    def __init__(self, f):
        super(Moov, self).__init__(f)


class Mvhd(FullBox):
    """
    aligned(8) class MovieHeaderBox extends FullBox(‘mvhd’, version, 0) {
        if (version==1) {
            unsigned int(64) creation_time;
            unsigned int(64) modification_time;
            unsigned int(32) timescale;
            unsigned int(64) duration;
        } else { // version==0
            unsigned int(32) creation_time;
            unsigned int(32) modification_time;
            unsigned int(32) timescale;
            unsigned int(32) duration;
        }
        template int(32) rate = 0x00010000; // typically 1.0
        template int(16) volume = 0x0100; // typically, full volume
        const bit(16) reserved = 0;
        const unsigned int(32)[2] reserved = 0;
        template int(32)[9] matrix =
        { 0x00010000,0,0,0,0x00010000,0,0,0,0x40000000 };
        // Unity matrix
        bit(32)[6] pre_defined = 0;
        unsigned int(32) next_track_ID;
    }
    """
    def __init__(self, f):
        super(Mvhd, self).__init__(f)

        if self.version == 1:
            self.creation_time = read_value(f, 64)
            self._bytecount += 8
            self.modification_time = read_value(f, 64)
            self._bytecount += 8
            self.timescale = read_value(f, 32)
            self._bytecount += 4
            self.duration = read_value(f, 64)
            self._bytecount += 8
        else:
            self.creation_time = read_value(f, 32)
            self._bytecount += 4
            self.modification_time = read_value(f, 32)
            self._bytecount += 4
            self.timescale = read_value(f, 32)
            self._bytecount += 4
            self.duration = read_value(f, 32)
            self._bytecount += 4

        self.rate = str(read_value(f, 16, "signed"))
        self.rate += '.'
        self.rate += str(read_value(f, 16, "signed"))
        self._bytecount += 4

        self.volume = str(read_value(f, 8, "signed"))
        self.volume += '.'
        self.volume += str(read_value(f, 8, "signed"))
        self._bytecount += 2

        read_value(f, 16, "void")
        self._bytecount += 2

        for i in xrange(2):
            read_value(f, 32)
            self._bytecount += 4

        self.matrix = []
        for i in xrange(9):
            self.matrix.append(read_value(f, 32, "signed"))
            self._bytecount += 4

        for i in xrange(6):
            read_value(f, 32)
            self._bytecount += 4

        self.next_track_ID = read_value(f, 32)
        self._bytecount += 4


class Stbl(ContainerBox):
    def __init__(self, f):
        super(Stbl, self).__init__(f)


class Stco(FullBox):
    """
    aligned(8) class ChunkOffsetBox
        extends FullBox(‘stco’, version = 0, 0) {
        unsigned int(32) entry_count;
        for (i=1; i <= entry_count; i++) {
            unsigned int(32) chunk_offset;
        }
    }
    """
    def __init__(self, f):
        super(Stco, self).__init__(f)

        self.entry_count = read_value(f, 32)
        self._bytecount += 4

        self.chunk_offset = []
        idx = 1
        while idx <= self.entry_count:
            self.chunk_offset.append(read_value(f, 32))
            self._bytecount += 4
            idx += 1


class Stsc(FullBox):
    """
    aligned(8) class SampleToChunkBox
        extends FullBox(‘stsc’, version = 0, 0) {
        unsigned int(32) entry_count;
        for (i=1; i <= entry_count; i++) {
            unsigned int(32) first_chunk;
            unsigned int(32) samples_per_chunk;
            unsigned int(32) sample_description_index;
        }
    }
    """
    class stc:
        def __init__(self):
            self.first_chunk = 0
            self.samples_per_chunk = 0
            self.sample_description_index = 0

    def __init__(self, f):
        super(Stsc, self).__init__(f)

        self.entry_count = read_value(f, 32)
        self._bytecount += 4

        self.stclist = []
        idx = 1
        while idx <= self.entry_count:
            temp = Stsc.stc()

            temp.first_chunk = read_value(f, 32)
            self._bytecount += 4

            temp.samples_per_chunk = read_value(f, 32)
            self._bytecount += 4

            temp.sample_description_index = read_value(f, 32)
            self._bytecount += 4

            self.stclist.append(temp)

            idx += 1

    def get_pair_from_sample(self, sample_idx):
        """
        :param self: self
        :param sample_idx: 1 based sample index
        :return (a, b):
                a is the index of input sample's chunk
                b is the index of first sample in that chunk
        """
        if sample_idx <= 0 or len(self.stclist) == 0:
            return 0, 0

        sampleCount = 0
        idx = 0
        while idx < len(self.stclist) - 1:
            nextSampleCount = ((self.stclist[idx + 1].first_chunk - self.stclist[idx].first_chunk) *
                               self.stclist[idx].samples_per_chunk +
                               sampleCount)
            if sample_idx <= nextSampleCount:
                break
            else:
                sampleCount = nextSampleCount

            idx += 1

        chunkIdxOffset = (sample_idx - sampleCount - 1) / self.stclist[idx].samples_per_chunk
        chunkIdx = chunkIdxOffset + self.stclist[idx].first_chunk
        startSampleIdxInChunk = sampleCount + chunkIdxOffset * self.stclist[idx].samples_per_chunk + 1
        return chunkIdx, startSampleIdxInChunk

    def get_chunk_index(self, sample_index):
        return self.get_pair_from_sample(sample_index)[0]

    def get_start_sample_index_in_chunk(self, sample_index):
        return self.get_pair_from_sample(sample_index)[1]


class Stss(FullBox):
    """
    aligned(8) class SyncSampleBox
        extends FullBox(‘stss’, version = 0, 0) {
        unsigned int(32) entry_count;
        int i;
        for (i=0; i < entry_count; i++) {
            unsigned int(32) sample_number;
        }
    }
    """
    def __init__(self, f):
        super(Stss, self).__init__(f)

        self.entry_count = read_value(f, 32)
        self._bytecount += 4

        self.sample_number = []
        for idx in xrange(self.entry_count):
            self.sample_number.append(read_value(f, 32))
            self._bytecount += 4


class Stsz(FullBox):
    """
    aligned(8) class SampleSizeBox extends FullBox(‘stsz’, version = 0, 0) {
        unsigned int(32) sample_size;
        unsigned int(32) sample_count;
        if (sample_size==0) {
            for (i=1; i <= sample_count; i++) {
                unsigned int(32) entry_size;
            }
        }
    }
    """
    def __init__(self, f):
        super(Stsz, self).__init__(f)

        self.sample_size = read_value(f, 32)
        self._bytecount += 4

        self.sample_count = read_value(f, 32)
        self._bytecount += 4

        self.entry_size = []
        if self.sample_size == 0:
            for idx in xrange(self.sample_count):
                self.entry_size.append(read_value(f, 32))
                self._bytecount += 4

    def get_sample_size(self, sample_index):
        """
        :param self: self
        :param sample_index: 1 based sample index value
        :return: size of sample, None when index invalid
        """
        if sample_index <= 0 or sample_index > self.sample_count:
            return None

        if self.sample_size != 0:
            return self.sample_size
        else:
            return self.entry_size[sample_index - 1]


class Tkhd(FullBox):
    """
    aligned(8) class TrackHeaderBox
        extends FullBox(‘tkhd’, version, flags){
        if (version==1) {
            unsigned int(64) creation_time;
            unsigned int(64) modification_time;
            unsigned int(32) track_ID;
            const unsigned int(32) reserved = 0;
            unsigned int(64) duration;
        } else { // version==0
            unsigned int(32) creation_time;
            unsigned int(32) modification_time;
            unsigned int(32) track_ID;
            const unsigned int(32) reserved = 0;
            unsigned int(32) duration;
        }
        const unsigned int(32)[2] reserved = 0;
        template int(16) layer = 0;
        template int(16) alternate_group = 0;
        template int(16) volume = {if track_is_audio 0x0100 else 0};
        const unsigned int(16) reserved = 0;
        template int(32)[9] matrix=
            { 0x00010000,0,0,0,0x00010000,0,0,0,0x40000000 };
            // unity matrix
        unsigned int(32) width;
        unsigned int(32) height;
    }
    """
    def __init__(self, f):
        super(Tkhd, self).__init__(f)

        if self.version == 1:
            self.creation_time = read_value(f, 64)
            self._bytecount += 8
            self.modification_time = read_value(f, 64)
            self._bytecount += 8
            self.track_ID = read_value(f, 32)
            self._bytecount += 4
            read_value(f, 32, "void")
            self._bytecount += 4
            self.duration = read_value(f, 64)
            self._bytecount += 8
        else:
            self.creation_time = read_value(f, 32)
            self._bytecount += 4
            self.modification_time = read_value(f, 32)
            self._bytecount += 4
            self.track_ID = read_value(f, 32)
            self._bytecount += 4
            read_value(f, 32, "void")
            self._bytecount += 4
            self.duration = read_value(f, 32)
            self._bytecount += 4

        for idx in xrange(2):
            read_value(f, 32, "void")
            self._bytecount += 4

        self.layer = read_value(f, 16, "signed")
        self._bytecount += 2

        self.alternate_group = read_value(f, 16, "signed")
        self._bytecount += 2

        self.volume = read_value(f, 16, "signed")
        self._bytecount += 2

        read_value(f, 16, "void")
        self._bytecount += 2

        self.matrix = []
        for idx in xrange(9):
            self.matrix.append(read_value(f, 32, "signed"))
            self._bytecount += 4

        self.width = read_value(f, 32, "fix_point")
        self._bytecount += 4
        self.height = read_value(f, 32, "fix_point")
        self._bytecount += 4


class Trak(ContainerBox):
    def __init__(self, f):
        super(Trak, self).__init__(f)


BoxDict = {}
BoxDict['co64'] = Co64
BoxDict['free'] = Free
BoxDict['ftyp'] = Ftyp
BoxDict['hdlr'] = Hdlr
BoxDict['mdia'] = Mdia
BoxDict['minf'] = Minf
BoxDict['moov'] = Moov
BoxDict['mvhd'] = Mvhd
BoxDict['stbl'] = Stbl
BoxDict['stco'] = Stco
BoxDict['stsc'] = Stsc
BoxDict['stss'] = Stss
BoxDict['stsz'] = Stsz
BoxDict['trak'] = Trak
BoxDict['tkhd'] = Tkhd