
## RedFile (redundant file) 

redfile is a archiving program, that takes in a file (whose contents warrant extra protection) and produces a larger file with redundant error correcting information. 

Once you have produced a redfile archive, you can burn it to a disc or save it on a hard drive, and know that even if the underlying physical media undergoes heavy damage such that most of its data is corrupted and the filesystem structure is lost, you can still recover the original data that was passed to redfile.

The UI will allow you to specify a replica count, the higher you set this number the better chance of data recovery you have (but also the larger the output file will be). 

The redfile format is very resilient to all kinds of errors. A redfile arkive can take corruption and data loss at the start of an arkive, at the end, any other place in the file, It can get re-ordered, shuffled around, mixed and matched with another redfile arkive, and still recovered. 

Inside the redfile arkive, There is no special block, such as superblock, directory, inode, or anything like that. Every block is just as important or discardable as any other block, and each block is replicated as many times as the user specified with the replica count option. As long as a single replica of each block survives the original data can be recovered. 

### To run:
download (or clone this repo), go the top directory and run:

python redfilegui.py

(to run the GUI you need python and Tkinter which comes with python installation on windows)
or 

python redfilecli.py

for example: 
python redfilecli -c -i pic1.jpg -o 1.rf -r 5

'-c' means create. this will produce a file called '1.rf' which will be approximately 5 times the size of pic1.jpg with 5 times replication to help it survive corruption and data loss. 

to get your data back:
python redfilecli -x -i 1.rf -o pic1.jpg
