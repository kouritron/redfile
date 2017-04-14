



import os
import sys


# if you got module not found errors, uncomment these. PyCharm IDE does not need it.
# get the abs version of . and .. and append them to this process's path.
sys.path.append(os.path.abspath('..'))
sys.path.append(os.path.abspath('.'))

#print sys.path

import unittest
import subprocess

import librf
from testutils import get_file_hash, make_file_with_random_content, find_file_within_this_project



class TestRedFileCli(unittest.TestCase):



    # This will run once for all tests in this class,
    @classmethod
    def setUpClass(cls):

        super(TestRedFileCli, cls).setUpClass()
        print "---------------------- setUpClass() called"

        cls.testfiles = ['1k.rand_bin', '1MB.rand_bin', '10MB.rand_bin']

        make_file_with_random_content(cls.testfiles[0], 1024)
        make_file_with_random_content(cls.testfiles[1], 1024 * 1024)
        make_file_with_random_content(cls.testfiles[2], 10 * 1024 * 1024)


    @classmethod
    def tearDownClass(cls):
        super(TestRedFileCli, cls).tearDownClass()
        print "---------------------- tearDownClass() called"

        files_to_remove = []
        for testfile in cls.testfiles:
            files_to_remove.append(testfile)
            files_to_remove.append(testfile + '.redfile')
            files_to_remove.append(testfile + '.redfile.recovered')


        for file in files_to_remove:
            try:
                os.remove(file)
            except OSError:
                pass


    # setUp will run once before every testcase
    def setUp(self):
        pass

    # tearDown will run once after every testcase
    def tearDown(self):
        pass



    def test_non_damaged_random_files_recovered_correctly(self):

        # run redfile cli to make .redfile
        # run redfile cli to recover
        # check the recovered file hashes the same as original.


        rfcli_path = find_file_within_this_project("redfilecli.py")
        print rfcli_path


        # python redfilecli.py -c -i ./tests/sample_files/pic1.jpg -o ark1.rf
        for testfile in self.testfiles:
            cmd = 'python ' + rfcli_path + ' -c -i ./' + testfile + ' -o ' + testfile + '.redfile'
            print cmd
            subprocess.call(cmd, shell=True)

        # python redfilecli.py -x -i ark1.rf -o orig1.jpg
        for testfile in self.testfiles:
            cmd = 'python ' + rfcli_path + ' -x -i ./' + testfile + '.redfile -o ' + testfile + '.redfile.recovered'
            print cmd
            subprocess.call(cmd, shell=True)


        for testfile in self.testfiles:
            original_fingerprint = get_file_hash(testfile)
            recovered_fingerprint = get_file_hash(testfile + '.redfile.recovered')

            self.assertEqual(original_fingerprint, recovered_fingerprint, 'Arkive did not recover correctly.')


    def test_minimally_damaged_random_files_recovered_correctly(self):

        pass


    def test_first_half_second_half_swapped_file_recovered_correctly(self):

        pass


    def test_file_smaller_than_one_unit_recovered_correctly(self):

        pass

    def test_file_smaller_than_one_unit_recovered_correctly(self):

        pass



if __name__ == '__main__':
    unittest.main()