

import hashlib

from rfutil import estream

def get_hash(src_bytes):
    hash_func = hashlib.sha256()
    hash_func.update(src_bytes)

    # this will return a string "0f20....."
    # return hash_func.hexdigest()

    # this is the actual bytes (i.e. (15, 32, ...)) (maybe still as a str object tho)
    # hash_func.hexdigest().decode('hex') == hash_func.digest()
    return hash_func.hexdigest()


def test_hash():
    print "----------------------------------------------------------------"

    test22321_str = b'Hello World\n'
    test1_str = b'\Hello World'
    test2_str = b'\x00\x00\x00\x00\x00\x00\x00\x00Hello World'
    # test2 sha256  is  add1cbde5f210aed97cc2bce0699daaec734c88326d43c38d6427c6699e60f7b


    print get_hash(test1_str)
    print get_hash(test2_str)



if "__main__" == __name__:
    test_hash()



    print 'hi'