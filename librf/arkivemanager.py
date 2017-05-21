
import hashlib
import struct
import os
import layoutmanager
import random
import shutil


_REPLICA_COUNT_DEFAULT = 4
_REPLICA_COUNT_MIN = 2
_BLOCK_SIZE_DEF = 512
_BLOCK_SIZE_MIN = 256
_BLOCK_SIZE_MAX = 60000

def _debug_msg(msg):

    #print(msg)
    pass

def _get_hash(src_bytes):
    hash_func = hashlib.sha256()
    hash_func.update(src_bytes)

    # this will return a string "0f20....."
    # return hash_func.hexdigest()

    # this is the actual bytes (as ints between [0,255] ) (maybe still as a str object tho in py 2 at least)
    # hash_func.hexdigest().decode('hex') == hash_func.digest()

    # digest() returns a <type 'str'> in python 2.7, and a <class 'bytes'> in python 3.x
    return hash_func.digest()


class Layout(object):
    """" Enumerate different physical layout managers that are exported by the module. """

    DISTRIBUTED = 1
    SEQUENTIAL = 2
    RANDOM = 3



class RFArkiver(object):

    # -------------------------------------------------------- class variables:
    # 129 == 0x81
    # FLAG_BYTE = 129
    FLAG_SEQ = b'\x81\x81\x81\x81\x81\x81'

    HEADER_SIZE = 80


    # careful with argument defaults, they are evaluated once at function definition, not every time its called
    # good practice to avoid using mutable objects for argument defaults.
    def __init__(self, replica_count=None, progress_callback=None, bs=None, layout=None):
        """ Initialize a new RF arkiver creator with the given options. 
        
        args:
        
        progress_callback >> a function that will be called by this RF arkiver several times during its operation
        to report a progress so far percentage. (useful for implementing a progress bar on the UI).
        bs >> physical block size to use.
        layout >> the choise of physical layout manager.
        replica_count >> the number of times to replicate each block. 
        """

        super(RFArkiver, self).__init__()
        self.progress_callback = progress_callback

        if replica_count and isinstance(replica_count, int) and (replica_count > _REPLICA_COUNT_MIN):
            self.REPLICA_COUNT = replica_count
        else:
            self.REPLICA_COUNT = _REPLICA_COUNT_DEFAULT


        #_debug_msg("++++++++++ cwd: " + str(os.getcwd()))

        # presumably the user will set this to something like 512 or 4k as the device min block size
        # we want this to be large enough such that the header overhead is about 10% or less, but not too large
        # such that the packets fail to deliver forward progress.
        # this should also never be set to less than 256 or even 512. higher than 4k is also not recommended,
        # higher than 64k is disallowed (wont fit in the 2 byte len field)

        if bs and isinstance(bs, int) and (bs >= _BLOCK_SIZE_MIN) and (bs < _BLOCK_SIZE_MAX):
            self.MAX_PACKET_SIZE = bs
        else:
            self.MAX_PACKET_SIZE = _BLOCK_SIZE_DEF


        # example: 512 - 80 == 432
        self.READ_SIZE = self.MAX_PACKET_SIZE - self.HEADER_SIZE

        # memorize the layout choice if it was valid.
        if layout and layout in {Layout.DISTRIBUTED, Layout.SEQUENTIAL, Layout.RANDOM}:
            self.layout_choice = layout
        else:
            self.layout_choice = Layout.DISTRIBUTED





    def _make_packet(self, src_br, source_offset):
        """ Given a few bytes (src_br) and an offset of the source file from which these bytes were read,
        make a packet (or call it page) that will go into the output carrying as payload the src bytes, along with
        any necessary header info. """

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
        packet_after_cksum_mutable.extend( self.src_fp )

        # add the actual source
        packet_after_cksum_mutable.extend(src_br)

        # done constructing the after cksum part, freeze it.
        packet_after_cksum_immutable = bytes(packet_after_cksum_mutable)

        packet_mutable.extend(_get_hash(packet_after_cksum_immutable))
        packet_mutable.extend(packet_after_cksum_immutable)

        return bytes(packet_mutable)


    def redundantize_and_save(self, src_filename, out_filename=None):
        """ Given the pathname of src file and output file. make a redudant file from src and save it into output.
        """
        # check if such a file exists or not. use these:
        # os.path.isfile    returns true if a file (or link to file is there)
        # os.path.isdir     returns true if a directory (or link to directory is there)
        # os.path.exists    returns true if either file or directory exists (or sym links)
        if os.path.isfile(src_filename):
            self.src_filename = src_filename
        else:
            raise ValueError('No such file. you supplied src filepath: ' + str(src_filename))

        # open the file and and save the handle in this object.
        self.infile = open(self.src_filename, "rb")

        # find src file size first.
        self.infile.seek(0, os.SEEK_END)
        infile_size = self.infile.tell()
        self.infile.seek(0, os.SEEK_SET)

        # compute the hash of the entire source file:
        hash_func = hashlib.sha256()
        chunk = bytes(self.infile.read(4096))
        while len(chunk) > 0:
            hash_func.update(chunk)
            chunk = bytes(self.infile.read(4096))

        self.src_fp = hash_func.digest()
        _debug_msg("the sha256 fingerprint of src file appears to be: " + str(self.src_fp.encode('hex')))

        # reset seek location back to the beginning of the file
        self.infile.seek(0, os.SEEK_SET)

        _debug_msg("source file appears to be: " + str(infile_size) + " bytes")
        infile_size_rounded_up = 0

        if infile_size % self.READ_SIZE == 0:
            infile_size_rounded_up = infile_size
        else:
            # // is unconditionally the integer division with truncate operator.
            infile_size_rounded_up = ((infile_size // self.READ_SIZE) + 1) * self.READ_SIZE

        # _debug_msg("source file after getting packet size aligned is: " + str(infile_size_rounded_up) + " bytes")

        self.total_packet_count = infile_size_rounded_up // self.READ_SIZE
        print("i believe i will need " + str(self.total_packet_count) + " packets. (not counting replication)")

        if Layout.SEQUENTIAL == self.layout_choice:
            self.layout_mgr = layoutmanager.SequentialLayoutManager(frame_size=self.MAX_PACKET_SIZE,
                replica_count=self.REPLICA_COUNT, total_page_count=self.total_packet_count, base_frame_num=0)

        elif Layout.RANDOM == self.layout_choice:
            self.layout_mgr = layoutmanager.RandomLayoutManager(frame_size=self.MAX_PACKET_SIZE,
                replica_count=self.REPLICA_COUNT, total_page_count=self.total_packet_count, base_frame_num=0)

        else:
            self.layout_mgr = layoutmanager.SequentialInterleavedDistributedBeginningsLayoutManager(
                frame_size=self.MAX_PACKET_SIZE, replica_count=self.REPLICA_COUNT,
                total_page_count=self.total_packet_count, base_frame_num=0)




        if out_filename is None:
            out_filename = str(self.src_filename) + ".rff"

        _debug_msg("--------------------------------------------------------------------------------------------------")
        _debug_msg("creating redundant file. output file name: " + out_filename)


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
                _debug_msg("Found short packet. len: " + str(len(packet)) + " I will pad this with 0s")
                packet_mutable = bytearray(packet)
                packet_mutable.extend( [0 for i in xrange(self.MAX_PACKET_SIZE - len(packet)) ] )
                packet = bytes(packet_mutable)

            offsets = self.layout_mgr.get_page_to_bytes_mappings(curr_packet_id)

            for i in range(len(offsets)):
                outfile.seek(offsets[i])
                outfile.write(packet)
                #_debug_msg("writing packet# " + str(packets_written) + " copy #" + str(i) +
                # " offset is: " + str(offsets[i]))


            curr_packet_id += 1
            src_br = bytearray(self.infile.read(self.READ_SIZE))

            # if a progress report call back is installed call it to give updates about progress so far
            # don't do this once for each packet, do it once in 100 or 1000 packets
            period = max(10, int(4000 // self.REPLICA_COUNT))
            if (0 == (curr_packet_id % period)) and (self.progress_callback):

                pct_complete = (float(curr_packet_id) / float(self.total_packet_count)) * 100

                #print "curr packet id is: " + str(float(curr_packet_id))
                #print "pct is: " + str(float(curr_packet_id) / float(self.total_packet_count))

                self.progress_callback( pct_complete )


        outfile.flush()

        outfile.seek(0, 2)
        _debug_msg("Redfile created. final size: " + str(outfile.tell()))
        _debug_msg("replica count: " + str(self.REPLICA_COUNT) + " -- total packets written: " + str(curr_packet_id))
        _debug_msg("##################################################################################################")

        # done with the loop
        outfile.close()
        self.infile.close()



class RFUnarkiver(object):

    def __init__(self, progress_callback=None):
        """ Init a new Red File arkive extractor. Takes in the filepath of where a potentially heavily damaged
        red file is.

         if progress_callback is supplied, during recovery, it will occassionally call that
         function with a number between 0 and 100 to indicate progress so far.
         """

        super(RFUnarkiver, self).__init__()
        self.progress_callback = progress_callback



    def _get_rand_name_with_size(self, size):
        """ Given positive int size, return a random name (file name/dir name) of len == size. """

        charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        charset_len = len(charset)
        result = 'rftmp_'

        for i in xrange(size):
            rand_idx = int(random.random() * charset_len)
            rand_char = charset[rand_idx:rand_idx + 1]
            result += rand_char

        return result

    def _choose_temp_dir_name(self, out_filename):

        # try to find a name with 6 random chars
        for i in xrange(100):
            temp_dir_name = self._get_rand_name_with_size(8)
            temp_dir_path = os.path.join(self.base_dir, temp_dir_name)
            # print "candidate for temp dir: " + temp_dir_path
            if not os.path.exists(temp_dir_path):
                print "found un-used name: "  + temp_dir_path
                return temp_dir_path

        # if that didnt work out, try to find a name with 16 random chars
        for i in xrange(100):
            temp_dir_name = self._get_rand_name_with_size(16)
            temp_dir_path = os.path.join(self.base_dir, temp_dir_name)
            # print "candidate for temp dir: " + temp_dir_path
            if not os.path.exists(temp_dir_path):
                print "found un-used name: "  + temp_dir_path
                return temp_dir_path



    def recover_and_save(self, src_filename, out_filename=None):
        """ Try to recover the original data and save it to out_filename. """


        # check if such a file exists or not. use these:
        # os.path.isfile    returns true if a file (or link to file is there)
        # os.path.isdir     returns true if a directory (or link to directory is there)
        # os.path.exists    returns true if either file or directory exists (or sym links)
        if os.path.isfile(src_filename):
            self.src_filename = src_filename
        else:
            raise ValueError('no such file exists.')

        # its possible that the file was on disk when the previous lines ran and no longer on disk now.
        # TODO maybe the above check is unnecessary, i kept in case we want to handle directories differently.
        self.infile = open(src_filename, "rb")

        # find the size of src file.
        self.infile.seek(0, os.SEEK_END)
        self.src_size = self.infile.tell()
        self.infile.seek(0, os.SEEK_SET)
        #print ">> xtractor believes its src file is: " + str(self.src_size) + " many bytes"

        if out_filename is None:
            out_filename = str(self.src_filename) + ".recovered"


        # make a temp directory to put the recovered file(s) in.
        self.base_dir = os.path.dirname(out_filename)
        if '' == self.base_dir:
            self.base_dir = '.'

        print "choosing temp dir. out_filename: " + str(out_filename)
        print "choosing temp dir. dir name is: " + str(self.base_dir)

        self.rftmp_dir = self._choose_temp_dir_name(out_filename=out_filename)

        # this could raise error if no perm to create directory among other things.
        # TODO handle this for the GUI, for cmd line ui its fine to just let the error propagate.
        os.makedirs(self.rftmp_dir)

        self.outfiles = {}

        _debug_msg("--------------------------------------------------------------------------------------------------")
        _debug_msg("recovering original file from red arkive. output filename: " + out_filename)


        potential_packet_start_offset = 0
        self.infile.seek(potential_packet_start_offset, os.SEEK_SET)
        readbuf_immutable = bytes(self.infile.read(6))

        bytes_processed_so_far = 0

        while len(readbuf_immutable) >= len(RFArkiver.FLAG_SEQ):
            # we got something process it.
            advance_len = -1

            if RFArkiver.FLAG_SEQ == readbuf_immutable[0: len(RFArkiver.FLAG_SEQ)]:
                # the len field is unsigned 16 int, hence max packet size is 2^16
                self.infile.seek(potential_packet_start_offset, os.SEEK_SET)
                readbuf_immutable = bytes(self.infile.read(66000))
                # suspect stage is complete in our suspect and confirm framing scheme.
                advance_len = self._check_for_valid_packet_and_process_if_found(readbuf_immutable)

            if advance_len > 0:
                # we successfully processed a packet, advance by advance_len many bytes
                potential_packet_start_offset += advance_len
                bytes_processed_so_far += advance_len
            else:
                # meaning no packet was found, advance our search by just one byte
                potential_packet_start_offset += 1
                bytes_processed_so_far += 1


            # advance into the file.
            self.infile.seek(potential_packet_start_offset, os.SEEK_SET)
            readbuf_immutable = bytes(self.infile.read(6))

            if( (self.progress_callback) and (0 == bytes_processed_so_far % 512000) ):
                pct_complete = float(bytes_processed_so_far) / float(self.src_size)
                pct_complete = pct_complete * 100
                #print ">> xtractor belief of pct complete: " + str(pct_complete)
                self.progress_callback(pct_complete)


        # if there is only one file handle in self.outfiles dict then move it out, rename it to what user gave us.
        # else rename the temp folder ___name user gave us_files___

        num_files_found = len(self.outfiles)
        for tmp_fname, tmp_fhandle in self.outfiles.items():
            tmp_fhandle.flush()
            tmp_fhandle.close()

        try:
            if 1 == num_files_found:
                # move the one file out from self.rftmp_dir to self.base_dir and del self.rftmp_dir
                tmp_fname, tmp_fhandle = self.outfiles.items()[0]
                shutil.move(src=os.path.join(self.rftmp_dir, tmp_fname),
                            dst=os.path.join(self.base_dir, os.path.basename(out_filename)))
                shutil.rmtree(path=self.rftmp_dir)
            elif 1 < num_files_found:
                # rename the folder whose path is in self.rftmp_dir
                shutil.move(self.rftmp_dir, out_filename)

        except OSError, e:
            print "Failed to perform clean up on the tmp directory."
            print e.strerror


        # delete the temp directory.
        # make sure to properly handle closing file handles before moving copying deleting.
        print "recover and save finished."





    def _get_dest_file_handle(self, dest_fingerprint):
        """ Given a sha256 fingerprint (hex str) of the file that is being recovered, find and return the 
        correct file handle for that file. """

        # print "file handle requested for file with fp: " + dest_fingerprint

        if self.outfiles.has_key(dest_fingerprint):
            return self.outfiles[dest_fingerprint]

        # lazily create the file handle, save it, and return it
        print "lazily creating new outfile for this fp: " + dest_fingerprint
        new_outfile_path = os.path.join(self.rftmp_dir, dest_fingerprint)
        new_outfile = open( new_outfile_path , 'wb')
        self.outfiles[dest_fingerprint] = new_outfile

        return self.outfiles[dest_fingerprint]



    def _check_for_valid_packet_and_process_if_found(self, possible_packet):
        """ Check if the supplied buffer containes a valid packet at the very beginning if so process it
          and return the number of bytes that got successfully processed. else return -1
          """

        # its not a valid packet, if i got less than a header size bytes
        if len(possible_packet) <= RFArkiver.HEADER_SIZE:
            return -1

        else:

            # we got something to process.
            # if this is a real packet. it should have these items in it (in order):
            # Field1: 6 bytes flag_seq
            # Field2: 2 bytes len field, (unsigned network byte order) (len of header and payload)
            # Field3: 32 bytes sha256 sum of the below fields
            # Field4: (after cksum) source offset -- index into the original source file where data
            #         was read from, 8 bytes unsigned network order
            # Field5: (after cksum) source file sha256 fingerprint.
            # Field6: (after cksum) source data
            # note that packet payload is field 4, 5 an 6 combined.

            field1_flag_seq = possible_packet[0:6]
            field2_len = struct.unpack("!H", possible_packet[6: 8])[0]
            field3_cksum = possible_packet[8: 40]

            # its not a valid packet, if it dont begin with flag sequence.
            if field1_flag_seq != RFArkiver.FLAG_SEQ:
                _debug_msg(">>>>>>>>>>> not valid because it doesnt start with flag seq. why was i called then??? ")
                return -1

            # its not a valid packet, if i have fewer bytes than the len field seems to indicate.
            if len(possible_packet) < field2_len:
                _debug_msg("not valid packet, because i seem to have fewer bytes than the len field says.")
                _debug_msg("I got: " + str(len(possible_packet)) + " len_field says: " + str(field2_len))
                return -1

            # if we haven't returned False we can say this.
            field4_source_offset = struct.unpack("!Q", possible_packet[40:48])[0]
            field5_source_fp = possible_packet[48:80]
            field6_source_data = possible_packet[80:field2_len]


            # if cksum confirms this packet's identity save its data at the offset it indicates.
            if bytes(field3_cksum) == bytes(_get_hash(possible_packet[40:field2_len])):


                # TODO dont save to outfile, use field5 to lazily get the correct file handle and save there.
                dest_filehandle = self._get_dest_file_handle(dest_fingerprint=field5_source_fp.encode('hex'))

                dest_filehandle.seek(field4_source_offset)
                dest_filehandle.write(field6_source_data)

                # TODO save somewhere the fact that this chunk was successfully recovered. (for forensic mode)
                # so we can do plots and shit

                return field2_len
            else:
                # hash failed
                return -1



def _log_progress(pct_complete=None):

    if pct_complete:
        pct_str = None
        try:
            pct_str = str(int(pct_complete)) + " %"
        except Exception as e:
            raise
        print "progress so far: " + pct_str



def try_del_files_at_base(base_dir, files):
    """ Try to delete files found in directory base_dir. if error was raised by os module try the next file
    in the files list. """

    for f in files:
        try:
            os.remove(base_dir + f)
        except OSError, e:
            print "Error cant delete: " + str(base_dir+f) + " reason: "
            print str(e.strerror)



def debug_run1():

    base_dir = "../tests/sample_files/"

    files = []
    files.append(("test1", 2))
    files.append(("test2", 2))
    files.append(("test3", 2))
    files.append(("test4", 2))
    files.append(("test5", 2))
    files.append(("pic1.jpg", 3))
    files.append(("pic2.jpg", 2))
    files.append(("pic3.png", 2))

    ra = None
    ru = None

    for fname, count in files:
        fname_full = base_dir + fname
        ra = RFArkiver( replica_count=count, progress_callback=_log_progress)
        ra.redundantize_and_save(src_filename=fname_full)
        ru = RFUnarkiver()
        ru.recover_and_save(src_filename=fname_full + ".redfile")

    # these are needed on windows to garbage collect last ra, ru right away
    # otherwise the last 2 files can't be deleted, because win fs api doesnt allow open files to be deleted (unix does)
    del ra
    del ru


    try_del_files_at_base(base_dir=base_dir, files=[f+'.redfile' for f, c in files])
    try_del_files_at_base(base_dir=base_dir, files=[f+'.redfile.recovered' for f, c in files])


if __name__ == '__main__':
    print "running arkivemanager"
    debug_run1()
