

""" redstream.py

"""

import hashlib
import struct
import os

import layoutmanager

_REPLICA_COUNT_DEFAULT = 3
_REPLICA_COUNT_MIN = 2


def _get_hash(src_bytes):
    hash_func = hashlib.sha256()
    hash_func.update(src_bytes)

    # this will return a string "0f20....."
    # return hash_func.hexdigest()

    # this is the actual bytes (as ints between [0,255] ) (maybe still as a str object tho in py 2 at least)
    # hash_func.hexdigest().decode('hex') == hash_func.digest()

    # digest() returns a <type 'str'> in python 2.7, and a <class 'bytes'> in python 3.x
    return hash_func.digest()



class RedArkiver:

    # 129 == 0x81
    # FLAG_BYTE = 129

    FLAG_SEQ = b'\x81\x81\x81\x81\x81\x81'

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

    # careful with argument defaults, they are evaluated once at function definition, not every time its called
    # good practice to avoid using mutable objects for argument defaults.
    def __init__(self, src_filename, replica_count=None):

        if replica_count is None:
            self.REPLICA_COUNT = _REPLICA_COUNT_DEFAULT
        elif (int == type(replica_count) and replica_count >= _REPLICA_COUNT_MIN):
            self.REPLICA_COUNT = replica_count
        else:
            raise ValueError('replica_count must be an int and >= ' + str(_REPLICA_COUNT_MIN))

        # check if such a file exists or not. use these:
        # os.path.isfile    returns true if a file (or link to file is there)
        # os.path.isdir     returns true if a directory (or link to directory is there)
        # os.path.exists    returns true if either file or directory exists (or sym links)
        if os.path.isfile(src_filename):
            self.src_filename = src_filename
        else:
            raise ValueError('no such file with the supplied filename was found')

        #  open the file and and save the handle in this object.
        self.infile = open(self.src_filename, "rb")

        # find src file size first.
        self.infile.seek(0, os.SEEK_END)
        infile_size = self.infile.tell()
        self.infile.seek(0, os.SEEK_SET)

        print "source file appears to be: " + str(infile_size) + " bytes"
        infile_size_rounded_up = 0

        if infile_size % self.READ_SIZE == 0:
            infile_size_rounded_up = infile_size
        else:
            # // is unconditionally the integer division with truncate operator.
            infile_size_rounded_up = ((infile_size // self.READ_SIZE) + 1) * self.READ_SIZE

        #print "source file after getting packet size aligned is: " + str(infile_size_rounded_up) + " bytes"

        total_packet_count = infile_size_rounded_up // self.READ_SIZE
        print "i believe i will need " + str(total_packet_count) + " packets in total"

        self.layout_mgr = layoutmanager.SequentialInterleavedDistributedBeginningsLayoutManager(
            frame_size=self.MAX_PACKET_SIZE, replica_count=self.REPLICA_COUNT, total_page_count=total_packet_count,
            base_frame_num=0)


    def _make_packet(self, src_br, source_offset):
        # create a bytearray for the redundant stream, byte array is mutable ( [] syntax works fine )
        packet_mutable = bytearray()
        packet_after_cksum_mutable = bytearray()


        # header starts with flag bytes
        packet_mutable.extend(self.FLAG_SEQ)


        # next is len field, 2 bytes unsigned, big endian. len of the overall packet (header + payload)
        packet_mutable.extend(struct.pack('!H', len(src_br) + self.HEADER_SIZE))

        # next is hash of the rest of the packet, this will be calculated later.

        # then we have a source byte offset as an unsigned 8 byte int.
        packet_after_cksum_mutable.extend(struct.pack('!Q', source_offset))

        # add the actual source
        packet_after_cksum_mutable.extend(src_br)

        # done constructing the after cksum part, freeze it.
        packet_after_cksum_immutable = bytes(packet_after_cksum_mutable)

        packet_mutable.extend(_get_hash(packet_after_cksum_immutable))
        packet_mutable.extend(packet_after_cksum_immutable)

        return bytes(packet_mutable)


    def redundantize_and_save(self, out_filename=None):
        """
        """

        if out_filename is None:
            out_filename = str(self.src_filename) + ".redfile"

        print "--------------------------------------------------------------------------------------------------------"
        print "creating redudant file. output file name: " + out_filename


        # open in and out files for reading in binary modem and writing in binary mode
        outfile = open(out_filename, "wb")


        # this offset indicates where in the source file current payload was read from.
        source_offset = 0
        curr_packet_id = 0

        # u can append an int (0,255) or extend using a bytes object.
        src_br = bytearray(self.infile.read(self.READ_SIZE))


        #while len(src_br) == self.READ_SIZE:
        while len(src_br) > 0:

            packet = self._make_packet(src_br, source_offset)
            source_offset += len(src_br)

            # now calculate how many times do we write this packet and where in output it should go.
            # dont worry about bad disk io pattern, we can implement a decent cached disk io later if the built in
            # buffering did not perform well.

            # this particular output layout needs to know the output filesize as part of its calculations
            # and it thus needs packets all to be the same size (the un-arkiver wont need this assumption tho)
            # note the padding isnt part of the packet. its just dead space before the next packet begins.
            if len(packet) < self.MAX_PACKET_SIZE:
                print "Found short packet. len: " + str(len(packet)) + " I will pad this with 0s"
                packet_mutable = bytearray(packet)
                packet_mutable.extend( [0 for i in xrange(self.MAX_PACKET_SIZE - len(packet)) ] )
                packet = bytes(packet_mutable)

            offsets = self.layout_mgr.get_page_to_bytes_mappings(curr_packet_id)

            for i in range(len(offsets)):
                outfile.seek(offsets[i])
                outfile.write(packet)
                #print "writing packet# " + str(packets_written) + " copy #" + str(i) + " offset is: " + str(offsets[i])


            curr_packet_id += 1
            src_br = bytearray(self.infile.read(self.READ_SIZE))

        outfile.flush()

        outfile.seek(0, 2)
        print "Redfile created. final size: " + str(outfile.tell())
        print "replica count: " + str(self.REPLICA_COUNT) + " -- total packets written: " + str(curr_packet_id)
        print "########################################################################################################"

        # done with the loop
        outfile.close()


class RedUnarkiver:

    def __init__(self, src_filename):

        # check if such a file exists or not. use these:
        # os.path.isfile    returns true if a file (or link to file is there)
        # os.path.isdir     returns true if a directory (or link to directory is there)
        # os.path.exists    returns true if either file or directory exists (or sym links)
        if os.path.isfile(src_filename):
            self.src_filename = src_filename
        else:
            raise ValueError('no such file with the supplied filename was found')

        # its possible that the file was on disk when the previous lines ran and no longer on disk now.
        # TODO maybe the above check is unnecessary, i kept in case we want to handle directories differently.
        self.infile = open(src_filename, "rb")

    def recover_and_save(self, out_filename=None):
        """
        """

        if out_filename is None:
            out_filename = str(self.src_filename) + ".recovered"

        self.outfile = open(out_filename, "wb")

        print "--------------------------------------------------------------------------------------------------------"
        print "recovering original file from red arkive. output filename: " + out_filename


        potential_packet_start_offset = 0
        self.infile.seek(potential_packet_start_offset, os.SEEK_SET)
        readbuf_immutable = bytes(self.infile.read(6))

        while len(readbuf_immutable) >= len(RedArkiver.FLAG_SEQ):
            # we got something process it.
            advance_len = -1

            if RedArkiver.FLAG_SEQ == readbuf_immutable[0: len(RedArkiver.FLAG_SEQ)]:
                # the len field is unsigned 16 int, hence max packet size is 2^16
                self.infile.seek(potential_packet_start_offset, os.SEEK_SET)
                readbuf_immutable = bytes(self.infile.read(66000))
                # suspect stage is complete in our suspect and confirm framing scheme.
                advance_len = self._check_for_valid_packet_and_process_if_found(readbuf_immutable)

            if advance_len > 0:
                # we successfully processed a packet, advance by advance_len many bytes
                potential_packet_start_offset += advance_len
            else:
                # meaning no packet was found, advance our search by just one byte
                potential_packet_start_offset += 1


            # advance into the file.
            self.infile.seek(potential_packet_start_offset, os.SEEK_SET)
            readbuf_immutable = bytes(self.infile.read(6))







    def _check_for_valid_packet_and_process_if_found(self, possible_packet):
        """ Check if the supplied buffer containes a valid packet at the very beginning if so process it
          and return the number of bytes that got successfully processed. else return -1
          """

        # its not a valid packet, if i got less than a header size bytes
        if len(possible_packet) <= RedArkiver.HEADER_SIZE:
            return -1

        else:

            # we got something to process.
            # if this is a real packet. it should have these items in it (in order):
            # Field1: 6 bytes flag_seq
            # Field2: 2 bytes len field, (unsigned network byte order) (len of header and payload)
            # Field3: 32 bytes sha256 sum
            # Field4: (after cksum) source offset -- index into the original source file where data
            #         was read from, 8 bytes unsigned network order
            # Field5: (after cksum) source data
            # note that packet payload is field 4 and 5 combined.

            field1_flag_seq = possible_packet[0:6]
            field2_len = struct.unpack("!H", possible_packet[6: 8])[0]
            field3_cksum = possible_packet[8: 40]

            # its not a valid packet, if it dont begin with flag sequence.
            if field1_flag_seq != RedArkiver.FLAG_SEQ:
                print ">>>>>>>>>>> not valid because it doesnt start with flag seq. why was i called then??? "
                return -1

            # its not a valid packet, if i have fewer bytes than the len field seems to indicate.
            if len(possible_packet) < field2_len:
                print "not valid packet, because i seem to have fewer bytes than the len field says."
                print "I got: " + str(len(possible_packet)) + " len_field says: " + str(field2_len)
                return -1

            # if we haven't returned False we can say this.
            field4_source_offset = struct.unpack("!Q", possible_packet[40:48])[0]
            field5_source_data = possible_packet[48:field2_len]


            # if cksum confirms this packet's identity save its data at the offset it indicates.
            if bytes(field3_cksum) == bytes(_get_hash(possible_packet[40:field2_len])):
                self.outfile.seek(field4_source_offset)
                self.outfile.write(field5_source_data)
                # TODO save somewhere the fact that this chunk was successfully recovered.
                # so we can do plots and shit

                return field2_len
            else:
                # hash failed
                return -1





def clean_up_sample_dir(orig_files):

    temp_files = []

    for fname in orig_files:
        temp_files.append(fname + ".redfile")
        temp_files.append(fname + ".redfile.recovered")

    for file in temp_files:
        try:
            os.remove(file)
        except OSError:
            pass




if __name__ == '__main__':

    base_dir = "../tests/sample_files/"

    files = []
    files.append(("test1", 2))
    files.append(("test2", 2))
    #files.append(("test3", 2))
    #files.append(("test4", 2))
    #files.append(("test5", 2))
    files.append(("pic1.jpg", 3))
    files.append(("pic2.jpg", 2))
    files.append(("pic3.png", 2))


    for fname, count in files:
        fname_full = base_dir + fname
        ra = RedArkiver(src_filename=fname_full, replica_count=count)
        ra.redundantize_and_save()
        ru = RedUnarkiver(src_filename=fname_full + ".redfile")
        ru.recover_and_save()


    #clean_up_sample_dir( [base_dir + fname   for fname, ignore in files ]  )


