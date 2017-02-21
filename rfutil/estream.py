

""" estream.py

A EscapeStream object can take a binary file (any file picture tarball text)
and produce a escaped version of it. Which is the same file as before except a certain flag byte's occurences
have been eliminated (escaped).

A EscapeStream object can also take an escaped file and return it to its former bit pattern.

The escaping is done similiar to the way some link layer protocols handle framing (PPP protocol for instance)

Or the escaping can be thought to be similiar to the way " and \ are escaped in printf format strings.

escaping rules (source to escaped stream)
assuming we have 3 characters.
flag (this is the byte we wish to abolish)
esc  (this is our escape byte)
rplflg (this is flag replacement byte)

src data                     >>>>>> becomes >>>>>>   escaped output
data .. flag .. data         >>>>>>>>>>>>>>>>>>>>>  data.. esc rplflg .. data
data .. esc .. data          >>>>>>>>>>>>>>>>>>>>>  data.. esc esc .. data
data .. esc flag .. data     >>>>>>>>>>>>>>>>>>>>>  data.. esc esc esc rplflg .. data
data .. esc esc .. data      >>>>>>>>>>>>>>>>>>>>>  data.. esc esc esc esc .. data
data .. rplflg .. data       >>>>>>>>>>>>>>>>>>>>>  data.. rplflg .. data
data .. esc rplflg .. data   >>>>>>>>>>>>>>>>>>>>>  data.. esc esc rplflg .. data

to reverse (un-escape) simply replace
esc rplflag   with   flag
esc esc       with   esc

and you should get back the orignial data
"""

class EscapeStream:
    def __init__(self):
        # read size in bytes
        self.READ_SIZE = 512

        # 0x80 == 128   -----  0x81 == 129  ------ 0x82 == 130
        self.RPLFLG_BYTE = 128
        self.FLAG_BYTE = 129
        self.ESCAPE_BYTE = 130


    def escape_and_save(self, in_file_name, out_file_name):
        """ Given a filename as input, read it, escape all occurences of flag byte and save the result
        on disk to another file.
        Also return the total number of bytes written to output file.
        """

        bytes_written = 0

        # open in and out files for reading in binary modem and writing in binary mode
        infile = open(in_file_name, "rb")
        outfile = open(out_file_name, "wb")

        # we can now use read(count) to read upto count many bytes from file into an str
        # python 2 strings can have binary data not just text.
        # iterating over a str will get u strings of len 1, iterating over byte array will get u ints
        src_br = bytearray(infile.read(self.READ_SIZE))

        while len(src_br) > 0:

            # create a bytearray for our escaped stream, byte array is mutable ( [] syntax works fine )
            # but watch for index out of range. but u can say .append() and .extend()
            escaped_br = bytearray()

            for b in src_br:
                #print b
                if b == self.ESCAPE_BYTE:
                    escaped_br.append(self.ESCAPE_BYTE)
                    escaped_br.append(self.ESCAPE_BYTE)
                elif b == self.FLAG_BYTE:
                    escaped_br.append(self.ESCAPE_BYTE)
                    escaped_br.append(self.RPLFLG_BYTE)
                else:
                    escaped_br.append(b)

            # bytes(escaped_br) returns a str in python 2, and something else (bytes object) in python 3
            # bytes object is not a string, but can be used as string in most places.
            outfile.write(bytes(escaped_br))
            bytes_written += len(escaped_br)
            src_br = bytearray(infile.read(self.READ_SIZE))

        # done with the loop
        outfile.close()

        return bytes_written

    def unescape_and_save(self, in_file_name, out_file_name):
        """ Given a filename as input, read it, un-escape all occurences of escaped flag bytes to recover
        the original and save the result on disk to another file.
        Also return the total number of bytes written to output file.
        """

        bytes_written = 0
        # open in and out files for reading in binary modem and writing in binary mode
        infile = open(in_file_name, "rb")
        outfile = open(out_file_name, "wb")

        # this is a bit more complicated than escape and save, we have to handle the case where the last
        # byte of one chunk and the first byte of the next chunk have to be processed together.
        src_br = bytearray(infile.read(self.READ_SIZE))
        # print "read " + str(len(src_br)) + " bytes"

        last_was_a_discarded_escape = False

        while len(src_br) > 0:

            # create a bytearray for our escaped stream, byte array is mutable ( [] syntax works fine )
            # but watch for index out of range. but u can say .append() and .extend()
            escaped_br = bytearray()

            for b in src_br:
                #print "idx: " + str(idx)

                if last_was_a_discarded_escape:
                    # we are reading the byte immediately after esc character

                    # clear this flag so we dont come back here again.
                    last_was_a_discarded_escape = False

                    if b == self.RPLFLG_BYTE:
                        escaped_br.append(self.FLAG_BYTE)
                    elif b == self.ESCAPE_BYTE:
                        escaped_br.append(self.ESCAPE_BYTE)
                    else:
                        print "Warning: Unexpected byte seen. Perhaps source is not a redfile escaped stream."
                        escaped_br.append(b)

                elif (b != self.ESCAPE_BYTE):
                    escaped_br.append(b)
                else:
                    # print "found escape byte, will not include it in the output."
                    last_was_a_discarded_escape = True



            # bytes(escaped_br) returns a str in python 2, and something else (bytes object) in python 3
            # bytes object is not a string, but can be used as string in most places.
            outfile.write(bytes(escaped_br))
            bytes_written += len(escaped_br)
            src_br = bytearray(infile.read(self.READ_SIZE))
            # print "read " + str(len(src_br)) + " bytes"

        # done with the loop
        outfile.close()
        return bytes_written



if __name__ == '__main__':

    print "------------------------------"
    es = EscapeStream()
    # es.escape_and_save("../sample_data/test2", "../sample_data/test2.escaped")
    # es.unescape_and_save("../sample_data/test2.escaped", "../sample_data/test2.escaped.unescaped")

    es.escape_and_save("../sample_data/pic1.jpg", "../sample_data/pic1.jpg.escaped")
    es.unescape_and_save("../sample_data/pic1.jpg.escaped", "../sample_data/pic1.jpg.escaped.unescaped")
