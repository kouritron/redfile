
# this fixes an issue with PyCharm IDE versions before 2017.1 (apparently 2017.1 fixed it)
from __future__ import absolute_import

import os
import sys
sys.path.insert(0, os.path.abspath('../src'))


import unittest

import estream

import hashlib




# ---------------------------------------------------- utility functions

def get_file_hash(filename):
    """ Return a str obj with the hex representation of the hash fingerprint
    of the file with the given filename.
    """
    READ_SIZE = 8192 * 4
    srcfile = open(filename, 'rb')
    hash_func = hashlib.sha256()
    buf = srcfile.read(READ_SIZE)
    while len(buf) > 0:
        hash_func.update(buf)
        buf = srcfile.read(READ_SIZE)
    return hash_func.hexdigest()


def make_file_with_random_content(filename, filesz):
    """ Create a binary file on disk filled with random content of filesz many bytes
    with the given filename
    """

    # fout = open(filename, 'wb')
    with open(filename, 'wb') as fout:
        fout.write(os.urandom(filesz))



class TestEscapeStream(unittest.TestCase):

    # This will run once for all tests in this class, setUp will run once before every testcase
    @classmethod
    def setUpClass(cls):

        super(TestEscapeStream, cls).setUpClass()
        # cls.static_resource = get_some_resource()
        print "---------------------- setUpClass() called"

        make_file_with_random_content('1k.rand_bin', 1024)
        make_file_with_random_content('1MB.rand_bin', 1024 * 1024)
        make_file_with_random_content('10MB.rand_bin', 10 * 1024 * 1024)

        # print get_file_hash('1k.rand_bin')

    @classmethod
    def tearDownClass(cls):
        super(TestEscapeStream, cls).tearDownClass()

        print "---------------------- tearDownClass() called"

        files = ['1k.rand_bin', '1k.rand_bin.escaped', '1k.rand_bin.escaped.unescaped',
                '1MB.rand_bin', '1MB.rand_bin.escaped', '1MB.rand_bin.escaped.unescaped',
                '10MB.rand_bin', '10MB.rand_bin.escaped', '10MB.rand_bin.escaped.unescaped']
        
        for file in files:
            try:
                os.remove(file)
            except OSError:
                pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_1k(self):

        rand_filename       = '1k.rand_bin'
        rand_filename_esc   = rand_filename + '.escaped'
        rand_filename_unesc = rand_filename_esc + '.unescaped'
        print " ------------------------------------------------ testing " + rand_filename

        orig_hash = get_file_hash(rand_filename)

        es = estream.EscapeStream()
        es.escape_and_save(rand_filename, rand_filename_esc )
        es.unescape_and_save(rand_filename_esc, rand_filename_unesc)

        escaped_then_unescaped = get_file_hash(rand_filename_unesc)

        self.assertEqual(orig_hash, escaped_then_unescaped)


    def test_1M(self):

        rand_filename       = '1MB.rand_bin'
        rand_filename_esc   = rand_filename + '.escaped'
        rand_filename_unesc = rand_filename_esc + '.unescaped'
        print " ------------------------------------------------ testing " + rand_filename

        orig_hash = get_file_hash(rand_filename)

        es = estream.EscapeStream()
        es.escape_and_save(rand_filename, rand_filename_esc )
        es.unescape_and_save(rand_filename_esc, rand_filename_unesc)

        escaped_then_unescaped = get_file_hash(rand_filename_unesc)

        self.assertEqual(orig_hash, escaped_then_unescaped)

    def test_10M(self):

        rand_filename       = '10MB.rand_bin'
        rand_filename_esc   = rand_filename + '.escaped'
        rand_filename_unesc = rand_filename_esc + '.unescaped'
        print " ------------------------------------------------ testing " + rand_filename

        orig_hash = get_file_hash(rand_filename)

        es = estream.EscapeStream()
        es.escape_and_save(rand_filename, rand_filename_esc )
        es.unescape_and_save(rand_filename_esc, rand_filename_unesc)

        escaped_then_unescaped = get_file_hash(rand_filename_unesc)

        self.assertEqual(orig_hash, escaped_then_unescaped)


    def test_3(self):
        self.assertTrue(True, "hi")

if __name__ == '__main__':
    unittest.main()