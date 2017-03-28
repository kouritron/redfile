



import os
import sys
import getopt

from librf import arkivemanager


def xtract_arkive(src_filename, out_filename):
    print "------------------------------------------------------------------------------------------------------------"
    print "xtracting arkive, plz standby. "
    print "input file: " + str(src_filename)
    print "output file: " + str(out_filename)

    xtractor = arkivemanager.RFUnarkiver(src_filename=src_filename)
    xtractor.recover_and_save(out_filename=out_filename)



def make_arkive(src_filename, out_filename):
    print "------------------------------------------------------------------------------------------------------------"
    print "creating arkive, plz standby. "
    print "input file: " + str(src_filename)
    print "output file: " + str(out_filename)

    # TODO receive replica count from command line and pass in here (dont leave to default)
    arkiver = arkivemanager.RFArkiver(src_filename=src_filename)
    arkiver.redundantize_and_save(out_filename=out_filename)



def main(arguments):
    version = "v0.8"
    usage_msg = "Welcome to redfile (redundant file) command line interface. This is version: " + version + """
    Usage: 
    ### create new redundant arkive.  
    $ ./redfile_cli -c -i <input filename> -o <output filename> -r <replication count:default 4, min: 2>
    
    ### extract original files from a redfile created arkive.  
    $ ./redfile_cli -x -i <input filename> -o <output filename>
    
    ### print this message.
    $ ./redfile_cli -v or -h 
    """

    src_filename = ''
    out_filename = ''

    # TODO enumerate this, op mode can be create arkive, extract arkive, and maybe a report or forensic mode, for now:
    # 1 is create
    # 2 is extract

    operation_mode = -1

    try:
        # the 1st is not a dict unfortunately, its a list of 2-tuples. the 2nd is everything left over, if any
        options_key_vals, left_over_args = getopt.getopt(args=arguments, shortopts="vhcxi:o:")
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
        make_arkive(src_filename=src_filename, out_filename=out_filename)
    elif 2 == operation_mode:
        xtract_arkive(src_filename=src_filename, out_filename=out_filename)


if __name__ == '__main__':
    main(sys.argv[1:])
























