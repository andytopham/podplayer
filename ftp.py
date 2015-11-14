#!/usr/bin/python
# ftp testing

import ftplib

ftp = ftplib.FTP('oldb','pi','raspberry')
filelist = ftp.dir()
print filelist
