#!/usr/bin/env python3
# ===================================================================================
# Project:    TropPo 
#             v. 1.0 2020-03-01, ICTP Wireless Lab
# Programmer: Marco Rainone - ICTP Wireless Lab
# Specifications, revisions and verifications:   
#             Marco Zennaro, Ermanno Pietrosemoli, Marco Rainone - ICTP Wireless Lab
# ===================================================================================
#
# The project is released with Mit License
# https://opensource.org/licenses/MIT
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# ===================================================================================
#
# Info
# ----------------------------------------------------------------
# the program receives as input the code of an igra radiosonde 
# and proceeds to download the archive with the "derived" data
# ftp://ftp.ncdc.noaa.gov/pub/data/igra/derived/
# see documentation:
# ftp://ftp.ncdc.noaa.gov/pub/data/igra/igra2-dataset-description.docx
# ftp://ftp.ncdc.noaa.gov/pub/data/igra/derived/igra2-derived-format.txt
#
# import required modules 
import os
import os.path
import getopt, errno, sys
import datetime

import ftplib

from zipfile import ZipFile

# -------------------------------------------------------------------------
# log igra derived
# -------------------------------------------------------------------------

# return to ftp start directory
def ftpIgraRootDir(ftp):
    ftp_position = ftp.pwd()
    if ftp_position == '/':
        # sei gia' nella radice 
        return
    # count n. '/' in ftp_position
    count = ftp_position.count('/')
    path = ""
    for i in range(count):
        path += '../'
    ftp.cwd(path)

# return to ftp igra base dir
def ftpIgraBaseDir(ftp):
    ftpIgraRootDir(ftp)
    ftp.cwd('pub/data/igra')              # change into "pub/data/igra" directory

# return to ftp igra dir with derived data 
def ftpIgraDerivedDir(ftp):
    ftpIgraRootDir(ftp)
    ftp.cwd('pub/data/igra/derived/derived-por/')              

# get igra station list
def getIgraStationList(ftp, dirIgraLog):
    # goto ftp igra base dir
    ftpIgraBaseDir(ftp)
    
    # get radiosonde list
    FileName = "igra2-station-list.txt"

    fpFileName = os.path.join(dirIgraLog, FileName)
    fileOut = open(fpFileName,'wb')
    op_completed = False
    try:
        print("... download: {} ...".format(FileName))
        ftp.retrbinary("RETR " + FileName ,fileOut.write)
        fileOut.close()
        op_completed = True
    except:
        print("Error ftp download file [{}]".format(FileName))
        fileOut.close()
        os.unlink(fpFileName)
    return(op_completed)
    
# get archive with Igra log
def getIgraDrvd(ftp, dirIgraLog, stationID):
    FileName = stationID + "-drvd.txt.zip"

    fpFileName = os.path.join(dirIgraLog, FileName)
    fileOut = open(fpFileName,'wb')
    op_completed = False
    try:
        print("... download: {} ...".format(FileName))
        ftp.retrbinary("RETR " + FileName ,fileOut.write)
        fileOut.close()
        op_completed = True
    except:
        print("Error ftp download file [{}]".format(FileName))
        fileOut.close()
        os.unlink(fpFileName)
    return(op_completed)

def igraDrvdExtract(dirIgraLog, stationID):
    # estrai dall'archivio zip il log igra
    # file name igra log archive
    fNameZipIgraLog = stationID + "-drvd" + ".txt.zip"
    fpZipIgraLog    = os.path.join(dirIgraLog, fNameZipIgraLog)     # full path zip

    with ZipFile(fpZipIgraLog, 'r') as zipObj:
       # Extract all the contents of zip file in dirIgraLog
       zipObj.extractall(dirIgraLog)

def igraDrvdCreateIndex(dirIgraLog, stationID):
    keySearch = "#" + stationID             # esempio: #TSM00060760
    print(keySearch)
    
    # file name igra log archive, without extension
    fNameIgraLog = stationID + "-drvd"
    # file name radiosonda log index
    fNameIgraIndex = fNameIgraLog
    fNameIgraIndex += '.idx'
    # file name radiosonda log
    fNameIgraLog += '.txt'
    fpIgraLog = os.path.join(dirIgraLog, fNameIgraLog)
    print(fpIgraLog)
    fpIgraIndex = os.path.join(dirIgraLog, fNameIgraIndex)
    print(fpIgraIndex)

    fIdx = open(fpIgraIndex, 'w')               # open file index to write
    # write header
    lineIdx = csv_sep + "date" + csv_sep + "pos_header" + csv_sep + "pos_data"  + csv_sep + "n_rec" + '\n'
    fIdx.write(lineIdx)

    # read file log Igra
    numHeader = -1          # n. row header con data/ora specificata
    numRecords = 0          # n. records for each section    
    with open(fpIgraLog,'r') as rsLog:
        rsLog.seek(0, os.SEEK_END)  # go to the end of the file.
        eof = rsLog.tell()          # get the end of file location
        rsLog.seek(0, os.SEEK_SET)  # go to the beginning of the file.
        while(rsLog.tell() != eof):
            pos = rsLog.tell()                  # posizione file prima della lettura riga
            line = rsLog.readline().strip()
            if line.startswith(keySearch)==False:
                numRecords +=1
                continue
            # -------------- new header
            if numHeader >=0:
                # save numRecords and reinit value
                lineIdx = csv_sep + str(numRecords) + '\n'
                fIdx.write(lineIdx)
                numRecords = 0          # n. records for each section    
                
            numHeader += 1                  # incrementa n. row header con data/ora specificata

            # init line to write in index file
            lineIdx = str(numHeader)
            
            # add time acquisition
            # YEAR         14- 17  Integer
            # MONTH        19- 20  Integer
            # DAY          22- 23  Integer
            # HOUR         25- 26  Integer
            # date_acq = line[13:26]
            date_acq = line[13:17]          # year
            date_acq += '-' + line[18:20]   # month
            date_acq += '-' + line[21:23]   # day
            date_acq += ' ' + line[24:26]   # hour
            date_acq += ':00:00'
            # lineIdx += csv_sep + '\"' + date_acq + '\"'
            lineIdx += csv_sep + date_acq
            
            lineIdx += csv_sep + str(pos)

            posStartData = rsLog.tell()     # posizione file dopo della lettura riga
            lineIdx += csv_sep + str(posStartData)
            fIdx.write(lineIdx)

    # save last numRecords value
    lineIdx = csv_sep + str(numRecords) + '\n'
    fIdx.write(lineIdx)
    rsLog.close()
    fIdx.close()
    # ------------------ end igraDrvdCreateIndex

# ---------------------------------------------------------------
# config
#
PathBaseDir = os.getcwd()               # current working directory of the process
access_rights = 0o777                   # define the access rights file/folder
csv_sep = ';'                           # char separator for csv

# -------------------------------------------------------------------------
#
# get full path file or directory
def get_full_path(file_folder_name):
    return (os.path.abspath(file_folder_name))

# check if the full path is file
def is_directory(full_path):
    # os.path.exists checks whether a file or directory exists:
    ris = os.path.exists(full_path)
    if ris:
        # os.path.isdir checks whether it's a directory
        return (os.path.isdir(full_path))
    return False            # the path is not directory

# check if the full path is file
def is_file_name(full_path):
    # os.path.exists checks whether a file or directory exists:
    ris = os.path.exists(full_path)
    if ris:
        # os.path.isdir checks whether it's a directory
        return (not os.path.isdir(full_path))
    return False            # the path is not filename

def get_dir_name(full_path):
    dirname = os.path.dirname(full_path)    # os independent
    return dirname

# return the file name without path
def get_file_name(full_path):
    basename = os.path.basename(full_path)  # os independent
    base = basename.split('.')[0]
    return base

# return the extension of file
def get_file_ext(full_path):
    basename = os.path.basename(full_path)  # os independent
    ext = '.'.join(basename.split('.')[1:])
    if ext == '.':
        return ""
    return ext

def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")

def printHlpOptions():
    print('{} -i <code ID radiosonda> -o <directory output>'.format(sys.argv[0]))

def printHlpFull():
    print('{} -i <code ID radiosonda> -o <directory output>'.format(sys.argv[0]))
    print('Download the igra derived data from:')
    print('ftp://ftp.ncdc.noaa.gov/pub/data/igra/derived/')
    print('Example:')
    print('{} -i GMM00010393 -o ./radio'.format(sys.argv[0]))
    print('Download GMM00010393-drvd.txt.zip in ./radio'.format(sys.argv[0]))

# -------------------------------------------------------------------------
# Get command-line arguments

# initialize variables
codeRadioSonda = ''
outDirRadioSonda = ''

try:
    opts, args = getopt.getopt(
            sys.argv[1:],
            'i:o:',
            ["inp=","out="])
except getopt.GetoptError:
    printHlpFull()              # print full help
    sys.exit(2)

nArg = 0
for opt, arg in opts:
    if opt == '-h':
        printHlpFull()              # print full help
        sys.exit()
    elif opt in ("-i", "--inp"):
        codeRadioSonda = arg
        print('Station string find: {}'.format(codeRadioSonda))
        nArg = nArg + 1
    elif opt in ("-o", "--out"):
        outDirRadioSonda = arg
        # print('Output directory csv result: {}'.format(outDirRadioSonda))
        nArg = nArg + 1
        
if nArg < 2:
    printHlpOptions()
    sys.exit()

if not os.path.exists(outDirRadioSonda):
    os.makedirs(outDirRadioSonda)

print("Station search: {}".format(codeRadioSonda))

codeRadioSonda = codeRadioSonda.lower()         # minuscolo

PathBaseDir = os.getcwd()               # current working directory of the process
access_rights = 0o777                   # define the access rights

# file name of phase ops
LstFile = "igra2-station-list.txt"
fpLstFile = os.path.join(outDirRadioSonda, LstFile)

print("search string: [{}] ...".format(codeRadioSonda))

nFiles = 0

# connect via ftp to igra
try:
    ftp = ftplib.FTP("ftp.ncdc.noaa.gov")
    ftp.login()
except:
    print("Error to connect Igra via ftp")
    sys.exit(2)

# goto ftp igra base dir
ftpIgraBaseDir(ftp)

# get radiosonde list
if getIgraStationList(ftp, outDirRadioSonda) == False:
    print("Error download file list: {}".format(LstFile))
    sys.exit(2)

print(ftp.pwd())
ftpIgraRootDir(ftp)
print(ftp.pwd())

# ftp.cwd('pub/data/igra/derived/derived-por/')              
# return to ftp igra dir with derived data 
ftpIgraDerivedDir(ftp)
print(ftp.pwd())
print("ftp://ftp.ncdc.noaa.gov/pub/data/igra/derived/derived-por")

with open(fpLstFile,'r') as fileRadioSonde:
    rs_list = list(fileRadioSonde)
    for lineStr in rs_list:
        str_id_sonda = lineStr[0:11]
        str_sonda = str_id_sonda.lower()
        if (str_sonda.find(codeRadioSonda) != -1):
            print("Found radiosonda: [{}]".format(str_id_sonda))
            # get file
            if getIgraDrvd(ftp, outDirRadioSonda, str_id_sonda):
                nFiles+=1

print(ftp.pwd())

print("Number of files downloaded: {}".format(nFiles))

# return error code
if nFiles == 0:
    # return error code
    sys.exit(errno.EACCES)
elif nFiles > 1:
    # Ok, n. elementi > 1
    #  the shell returns 'OK'
    sys.exit(0)

stationID = codeRadioSonda.upper()                    # radiosonda code
    
# -------------------------------------------------------------------------
igraDrvdExtract(outDirRadioSonda, stationID)

# -------------------------------------------------------------------------
igraDrvdCreateIndex(outDirRadioSonda, stationID)

#  the shell returns 'OK'
sys.exit(0)