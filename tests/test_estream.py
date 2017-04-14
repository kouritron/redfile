


import os
import sys


## if you got module not found errors, uncomment these. PyCharm IDE does not need it.
# add ../ and ./ to path, depending on what cwd was when python process was created, one of these might help find librf
sys.path.insert(0, os.path.abspath('../'))
sys.path.insert(0, os.path.abspath('./'))

#print sys.path


import os
import unittest
from testutils import get_file_hash, make_file_with_random_content
from librf import estream




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

        esc_filesz = 0
        unesc_filesz = 0

        es = estream.EscapeStream()
        esc_filesz = es.escape_and_save(rand_filename, rand_filename_esc )
        unesc_filesz = es.unescape_and_save(rand_filename_esc, rand_filename_unesc)

        escaped_then_unescaped = get_file_hash(rand_filename_unesc)

        self.assertEqual(orig_hash, escaped_then_unescaped)
        self.assertTrue(esc_filesz >= unesc_filesz)

        print "esc_filesz: " + str(esc_filesz)
        print "unesc_filesz: " + str(unesc_filesz)


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


    def test_flag_byte_should_not_exist_in_escaped_file(self):
        print " ------------------------------------------------ testing flag byte existence in escaped file"

        rand_filename       = '1k.rand_bin'
        rand_filename_esc   = rand_filename + '.escaped'

        es = estream.EscapeStream()
        es.escape_and_save(rand_filename, rand_filename_esc)


        with open(rand_filename_esc, 'rb') as fin:

            src_br = bytearray(fin.read(es.READ_SIZE))
            while len(src_br) > 0:
                for b in src_br:
                    self.assertNotEqual(b, es.FLAG_BYTE, "flag byte found in escaped file")

                src_br = bytearray(fin.read(es.READ_SIZE))

    def test_3(self):
        self.assertTrue(True, "hi")

if __name__ == '__main__':
    unittest.main()