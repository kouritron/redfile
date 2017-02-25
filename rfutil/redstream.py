

""" redstream.py

"""

import hashlib
import struct






class RedStream:

    # 129 == 0x81
    FLAG_BYTE = 129

    # class variables:
    # presumably the user will set this to something like 512 or 4k as the device min block size
    # we want this to be large enough such that the header overhead is about 10% or less, but not too large
    # such that the packets fail to deliver forward progress.
    # this should also never be set to less than 256 or even 512. higher than 4k is also not recommended,
    # higher than 64k is disallowed (wont fit in the 2 byte len field)
    MAX_PACKET_SIZE = 512
    HEADER_SIZE = 48

    # 512 - 48 == 464
    READ_SIZE = MAX_PACKET_SIZE - HEADER_SIZE

    #    def __init__(self):
    #        pass


    # static methods are not bound to anything, not even the class
    @staticmethod
    def get_hash(src_bytes):
        hash_func = hashlib.sha256()
        hash_func.update(src_bytes)

        # this will return a string "0f20....."
        # return hash_func.hexdigest()

        # this is the actual bytes (as ints between [0,255] ) (maybe still as a str object tho in py 2 at least)
        # hash_func.hexdigest().decode('hex') == hash_func.digest()
        return hash_func.digest()


    # class methods are bound to the class, static methods are not bound to anything. if u need to reference
    # the class name, i.e. RedStream.FLAG_BYTE use this so we dont have to hard code the class name.
    @classmethod
    def make_packet(cls, src_br, source_offset):
        # create a bytearray for the redundant stream, byte array is mutable ( [] syntax works fine )
        packet = bytearray()
        packet_after_cksum = bytearray()

        # header starts with flag bytes
        packet.append(cls.FLAG_BYTE)
        packet.append(cls.FLAG_BYTE)
        packet.append(cls.FLAG_BYTE)
        packet.append(cls.FLAG_BYTE)
        packet.append(cls.FLAG_BYTE)
        packet.append(cls.FLAG_BYTE)

        # next is len field, 2 bytes unsigned, big endian. len of the overall packet (header + payload)
        packet.extend(struct.pack('!H', len(src_br) + cls.HEADER_SIZE))

        # next is hash of the rest of the packet, this will be calculated later.

        # then we have a source byte offset as an unsigned 8 byte int.
        packet_after_cksum.extend(struct.pack('!Q', source_offset))

        # add the actual source
        packet_after_cksum.extend(src_br)

        packet.extend(cls.get_hash(packet_after_cksum))
        packet.extend(packet_after_cksum)

        return packet




    def redundantize_and_save(self, in_file_name, out_file_name):
        """
        """

        # print self.READ_SIZE

        bytes_written = 0

        # open in and out files for reading in binary modem and writing in binary mode
        infile = open(in_file_name, "rb")
        outfile = open(out_file_name, "wb")

        # find src file size first.
        infile.seek(0, 2)
        infile_size = infile.tell()
        infile.seek(0, 0)

        print "source file appears to be: " + str(infile_size) + " bytes"

        # u can append an int (0,255) or extend using a bytes object.
        src_br = bytearray(infile.read(self.READ_SIZE))

        # this offset indicates where in the source file current payload was read from.
        # this is more like bytes read from the source file before current packet.
        source_offset = 0

        #while len(src_br) == self.READ_SIZE:
        while len(src_br) > 0:

            packet = self.make_packet(src_br, source_offset)

            outfile.write(bytes(packet))
            bytes_written += len(packet)

            src_br = bytearray(infile.read(self.READ_SIZE))
            source_offset += len(src_br)

        # done with the loop
        outfile.close()

        print "total bytes written to output file: " + str(bytes_written)
        return bytes_written



if __name__ == '__main__':

    print "------------------------------"
    rs = RedStream()

    rs.redundantize_and_save("../sample_data/test1", "../sample_data/test1.redfile")
    rs.redundantize_and_save("../sample_data/pic1.jpg", "../sample_data/pic1.jpg.redfile")
