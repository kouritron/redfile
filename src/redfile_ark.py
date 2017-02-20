# redfile arkiver 

## TODO make a sliding window class, that opens the file for reading, exports a file interface
## allows its user to read one byte at a time.

## TODO make a py program that uses the sliding reader to read, escape bad chars and write back to disk



def test_read():

    # how many bytes to read in every read operation
    read_size = 1

    # open for reading as binary
    with open("../sample_data/test_32.hex", "rb") as sf:
        byte = sf.read(read_size)
        while byte:
            # Do  something with the byte
            print byte


            # read next byte
            byte = sf.read(read_size)


if "__main__" == __name__:

    print "----------------------------------------------------------------"
    test_read()






