

""" redstream.py

"""

import hashlib
import struct






class RedStream:

    # 129 == 0x81
    FLAG_BYTE = 129

    REDUNDANCY_LEVEL = 4

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

        print "--------------------------------------------------------------------------------------------------------"
        print "redundantize_and_save called on input file: " + in_file_name


        # open in and out files for reading in binary modem and writing in binary mode
        infile = open(in_file_name, "rb")
        outfile = open(out_file_name, "wb")

        # find src file size first.
        infile.seek(0, 2)
        infile_size = infile.tell()
        infile.seek(0, 0)

        print "source file appears to be: " + str(infile_size) + " bytes"
        infile_size_rounded_up = 0

        if infile_size % self.READ_SIZE == 0:
            infile_size_rounded_up = infile_size
        else:
            # // is unconditionally the integer division with truncate operator.
            infile_size_rounded_up = ((infile_size // self.READ_SIZE) + 1) * self.READ_SIZE

        print "source file after getting packet size aligned is: " + str(infile_size_rounded_up) + " bytes"

        total_packet_count = infile_size_rounded_up // self.READ_SIZE
        print "i believe i will need " + str(total_packet_count) + " packets in total"

        source_offset = 0
        packets_written = 0

        # u can append an int (0,255) or extend using a bytes object.
        src_br = bytearray(infile.read(self.READ_SIZE))


        # this offset indicates where in the source file current payload was read from.
        # this is more like bytes read from the source file before current packet.

        #while len(src_br) == self.READ_SIZE:
        while len(src_br) > 0:

            packet = self.make_packet(src_br, source_offset)
            source_offset += len(src_br)

            # now calculate how many times do we write this packet and where in output it should go.
            # dont worry about bad disk io pattern, we can implement a decent cached disk io later if the built in
            # buffering did not perform well.

            # this particular randomizer needs to know the output filesize as part of its calculations
            # and it thus needs packets all to be the same size (the un-arkiver wont need this assumption tho)
            if len(packet) < self.MAX_PACKET_SIZE:
                print "Found short packet. len: " + str(len(packet)) + " I will pad this with 0s"
                packet.extend( [0 for i in xrange(self.MAX_PACKET_SIZE - len(packet)) ] )


            copy1_offset = packets_written * self.MAX_PACKET_SIZE * self.REDUNDANCY_LEVEL
            outfile.seek(copy1_offset)
            outfile.write(bytes(packet))

            print "writing packet# " + str(packets_written) + " redundant copy1 offset is: " + str(copy1_offset)

            # write inverse sequential copy now.
            copy2_offset = ((total_packet_count - packets_written) * self.REDUNDANCY_LEVEL * self.MAX_PACKET_SIZE) \
                           - self.MAX_PACKET_SIZE

            outfile.seek(copy2_offset)
            outfile.write(bytes(packet))
            print "writing packet# " + str(packets_written) + " redundant copy2 offset is: " + str(copy2_offset)


            packets_written += 1

            src_br = bytearray(infile.read(self.READ_SIZE))

        outfile.flush()

        outfile.seek(0, 2)
        print "Done. new size is: " + str(outfile.tell()) + " total packets written: " + str(packets_written)
        print "########"

        # done with the loop
        outfile.close()



if __name__ == '__main__':


    rs = RedStream()

    rs.redundantize_and_save("../sample_data/test1", "../sample_data/test1.redfile")
    rs.redundantize_and_save("../sample_data/test2", "../sample_data/test2.redfile")
    rs.redundantize_and_save("../sample_data/test3", "../sample_data/test3.redfile")
    rs.redundantize_and_save("../sample_data/test4", "../sample_data/test4.redfile")
    rs.redundantize_and_save("../sample_data/test5", "../sample_data/test5.redfile")
    #rs.redundantize_and_save("../sample_data/pic1.jpg", "../sample_data/pic1.jpg.redfile")
