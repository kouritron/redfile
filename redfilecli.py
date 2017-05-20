



import os
import sys
import getopt

from librf import arkivemanager

def _get_current_version():

    version = None
    try:
        import librf._version as vm
        version = vm.__version__
    except:
        pass

    if not version:
        version = 'unknown'

    return version


def _progress_report_callback(pct_complete=None):
    """ Given a number between 0 and 100, indicating percentage of progress done so far,
    inform the user of the progress so far, by loggin to stdout. """

    if None == pct_complete:
        return

    if not (isinstance(pct_complete, int) or isinstance(pct_complete, float) ):
        return

    if (pct_complete < 0) or (pct_complete > 100):
        return

    try:
        pct_str = str(int(pct_complete)) + " %"
        print pct_str  + " Done"
    except:
        pass


def xtract_arkive(src_filename, out_filename):
    print "------------------------------------------------------------------------------------------------------------"
    print "xtracting arkive, plz standby. "
    print "input file: " + str(src_filename)
    print "output file: " + str(out_filename)

    xtractor = arkivemanager.RFUnarkiver(src_filename=src_filename, progress_callback=_progress_report_callback)
    xtractor.recover_and_save(out_filename=out_filename)



def make_arkive(src_filename, out_filename, replica_count):
    print "------------------------------------------------------------------------------------------------------------"
    print "creating arkive, plz standby. "
    print "input file: " + str(src_filename)
    print "output file: " + str(out_filename)

    # TODO receive replica count from command line and pass in here (dont leave to default)
    arkiver = arkivemanager.RFArkiver(src_filename=src_filename, replica_count=replica_count,
                                        progress_callback=_progress_report_callback)
    arkiver.redundantize_and_save(out_filename=out_filename)



def main(arguments):
    version = _get_current_version()
    usage_msg = "Welcome to redfile (redundant file) command line interface. This is version: " + version + """
    Usage:
    ### create new redundant arkive.
    $ ./redfilecli -c -i <input filename> -o <output filename> -r <replication count:default 4, min: 2>

    ### extract original files from a redfile created arkive.
    $ ./redfilecli -x -i <input filename> -o <output filename>

    ### print this message.
    $ ./redfilecli -v or -h
    """

    src_filename = ''
    out_filename = ''
    replica_count = 4

    # TODO enumerate this, op mode can be create arkive, extract arkive, and maybe a report or forensic mode, for now:
    # 1 is create
    # 2 is extract

    operation_mode = -1

    try:
        # the 1st is not a dict unfortunately, its a list of 2-tuples. the 2nd is everything left over, if any
        options_key_vals, left_over_args = getopt.getopt(args=arguments, shortopts="vhcxi:o:r:")
    except getopt.GetoptError:
        print usage_msg
        # 2 is usually meant for bad command line args.
        #  0 is for successful exit as usual. i could not find any named enums to use instead of raw numbers
        sys.exit(2)

    # print options_key_vals
    # print left_over_args

    for option_key, option_val in options_key_vals:
        if ('-h' == option_key) or ('-v' == option_key):
            print usage_msg
            sys.exit(0)

        if '-i' == option_key:
            src_filename = option_val

        if '-o' == option_key:
            out_filename = option_val

        if '-r' == option_key:
            arg_int = None
            try:
                arg_int = int(option_val)
            except:
                pass

            if (None == arg_int) or (arg_int < 2):
                print "replica count must be an int and >= 2"
                print usage_msg
                sys.exit(0)

            replica_count = arg_int


        # check if we need to create arkive
        if '-c' == option_key:
            if -1 != operation_mode:
                # multiple operation modes have been supplied, print usage and terminate
                print usage_msg
                sys.exit(2)
            # now set the operation mode
            operation_mode = 1

        # check if we need to extract arkive
        if '-x' == option_key:
            if -1 != operation_mode:
                # multiple operation modes have been supplied, print usage and terminate
                print usage_msg
                sys.exit(2)
            # now set the operation mode
            operation_mode = 2



    # TODO ideally we have an enum set and we would set if operation_mode not in possible modes.
    if ('' == src_filename) or ('' == out_filename) or (-1 == operation_mode):
        print usage_msg
        sys.exit(2)


    #print "cwd: " + str(os.getcwd())
    #print "input file: >>" + str(src_filename) + "<<"
    #print "output file: >>" + str(out_filename) + "<<"

    # TODO do we allow any file name of any length.
    # maybe we should stop at max filename length allowed by any of any major filesystem (min of NTFS, EXT2, UFS, FAT??)

    if 1 == operation_mode:
        make_arkive(src_filename=src_filename, out_filename=out_filename, replica_count=replica_count)
    elif 2 == operation_mode:
        xtract_arkive(src_filename=src_filename, out_filename=out_filename)


if __name__ == '__main__':
    main(sys.argv[1:])
