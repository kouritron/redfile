

import hashlib

from rfutil import estream

def get_hash(src_bytes):
    hash_func = hashlib.sha1()
    hash_func.update(src_bytes)
    return hash_func.hexdigest()



def test_hash():
    print "----------------------------------------------------------------"
    test1_sum = "0a4d55a8d778e5022fab701977c5d840bbc486d0"
    test1_str = b'Hello World'

    test2_sum = "648a6a6ffffdaa0badb23b8baf90b6168dd16b3a"
    test2_str = b'Hello World\n'

    print get_hash(test1_str)
    print get_hash(test2_str)



if "__main__" == __name__:

    test_filename = "sample_data/pic1.jpg"

    es = estream.EscapeStream()

    test_filesz =  es.escape_and_save("../sample_data/pic1.jpg", "../sample_data/pic1.jpg.escaped")




    print 'hi'