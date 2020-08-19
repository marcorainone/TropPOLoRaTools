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
# Receives:
# 1. log archive path of radiosonde
# 2. time in format year month day hour min
# 3. n. days of the radiosonde log to be analyzed
# The program extracts the data of the radiosonde acquisitions closest to the date provided 
# and generates html graphs of N, M and slope as a function of the height H reached by the balloon.
#
# import required modules 
import os
import os.path
import getopt, sys
import gc               # garbage collector
import time
from calendar import timegm
import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from staticmap import StaticMap, CircleMarker
from collections import namedtuple

import csv, json, sys
import geopy.distance
from array import *

import plotly
import plotly.graph_objs as go
import plotly.express as px

import ftplib

from zipfile import ZipFile

# ---------------------------------------------------------------
# see documentation:
# ftp://ftp.ncdc.noaa.gov/pub/data/igra/igra2-dataset-description.docx
# ftp://ftp.ncdc.noaa.gov/pub/data/igra/derived/igra2-derived-format.txt
# -------------------------------
# Variable        Columns Type  
# -------------------------------
# PRESS           1-  7   Integer
# REPGPH          9- 15   Integer   reported geopotential height (meters).
# CALCGPH        17- 23   Integer   calculated geopotential height (meters)
# TEMP           25- 31   Integer
# TEMPGRAD       33- 39   Integer
# PTEMP          41- 47   Integer
# PTEMPGRAD      49- 55   Integer
# VTEMP          57- 63   Integer
# VPTEMP         65- 71   Integer
# VAPPRESS       73- 79   Integer
# SATVAP         81- 87   Integer
# REPRH          89- 95   Integer
# CALCRH         97-103   Integer
# RHGRAD        105-111   Integer
# UWND          113-119   Integer
# UWDGRAD       121-127   Integer
# VWND          129-135   Integer
# VWNDGRAD      137-143   Integer
# N             145-151   Integer   the refractive index (unitless).
# -------------------------------
# 
# Notes:
# REPGPH 	reported geopotential height (meters). 
#         This value is often not available at significant levels.
# 		
# CALCGPH calculated geopotential height (meters). 
#         The geopotential height has been estimated by applying the hydrostatic balance to
# 		the atmospheric layer between the next lower level with a reported geopotential height and the current level.

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

def igraDrvdExtract(dirIgraLog, stationID):
    # estrai dall'archivio zip il log igra
    # file name igra log archive
    fNameZipIgraLog = stationID + "-drvd" + ".txt.zip"
    fpZipIgraLog    = os.path.join(dirIgraLog, fNameZipIgraLog)     # full path zip

    with ZipFile(fpZipIgraLog, 'r') as zipObj:
       # Extract all the contents of zip file in dirIgraLog
       zipObj.extractall(dirIgraLog)

# Extract the record time string from line of derived record
# return:
# string formatted time
# epoch time in seconds
#
def strDrvdRecordTime(line, yearLimit):
    # get string fields
    year  = line[13:17]             # year
    month = line[18:20]             # month
    day   = line[21:23]             # day
    hour  = line[24:26]             # hour
    # string date / time
    date_time_str  = year                # year
    date_time_str += '-' + month         # month
    date_time_str += '-' + day           # day
    date_time_str += ' ' + hour          # hour
    date_time_str += ':00:00'
    # if int(year)<1970:
    if int(year)<yearLimit:
        return(date_time_str, 0)
    # date after or equal yearLimit (standard: 1970)
    # date_time_obj = datetime.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')
    utc_time = time.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
    epoch_time = timegm(utc_time)
    return(date_time_str, epoch_time)
           
# from time string return time in "%Y%m%d%H%M%S", used to create filename
def time_compact(date_time_str):
    utc_time = time.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
    ris = time.strftime("%Y%m%d%H%M%S", utc_time)
    return(ris)

def igraDrvdCreateIndex(dirIgraLog, stationID, yearLimit=2015):
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

    # -------------------- write header
    lineIdx = "date" + csv_sep + "tm_epoch" + csv_sep + "pos_header" + csv_sep + "pos_data"  + csv_sep + "n_rec" + '\n'
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
            # extract time acquisition
            date_acq, epoch_time = strDrvdRecordTime(line, yearLimit)
            # verify if time before yearLimit
            if epoch_time == 0:
                # record time before limit
                # print("!!! Time before {}:[{}]".format(yearLimit, date_acq))
                numRecords = 0          # n. records for each section    
                posStartData = rsLog.tell()             # posizione file dopo della lettura riga
                continue
            # epoch time in limit
                
            # -------------- time new header is correct
            elif numHeader >= 0:
                # save numRecords and reinit value
                if numHeader == 0:
                    numRecords = 0
                lineIdx = csv_sep + str(numRecords) + '\n'
                fIdx.write(lineIdx)
                numRecords = 0          # n. records for each section    
            numHeader += 1                  # incrementa n. row header con data/ora specificata

            # -------------- init line to write in index file
            # lineIdx = str(numHeader)
            lineIdx = ""
            
            # create record to write csv
            # lineIdx += csv_sep + '\"' + date_acq + '\"'
            lineIdx += date_acq                     # date, time string
            lineIdx += csv_sep + str(epoch_time)    # epoch time
            
            lineIdx += csv_sep + str(pos)           # position header in file
            posStartData = rsLog.tell()             # posizione file dopo della lettura riga
            lineIdx += csv_sep + str(posStartData)

            fIdx.write(lineIdx)                     # write record in csv

    # save last numRecords value
    lineIdx = csv_sep + str(numRecords) + '\n'
    fIdx.write(lineIdx)
    rsLog.close()
    fIdx.close()
    # ------------------ end igraDrvdCreateIndex


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")

def printHlpOptions():
    print('{} -i <zip Igra2 derived log file> -t <string time> -d <n. days>'.format(sys.argv[0]))

def printHlpFull():
    print('{} -i <zip Igra2 derived log file> -t <string time> -d <n. days>'.format(sys.argv[0]))
    print('Download the Igra2 derived data from:')
    print('ftp://ftp.ncdc.noaa.gov/pub/data/igra/derived/')
    print('Example:')
    print('{} -i radio/GMM00010393-drvd.txt.zip -t \"2020 02 16 00 00\" -d 7'.format(sys.argv[0]))
    print('Decompress radio/GMM00010393-drvd.txt.zip'.format(sys.argv[0]))
    print('Read measurements starting from \"2020-02-16 00:00\" for 7 days')


# -------------------------------------------------------------------------
# Get command-line arguments

# initialize variables
inpZipIgraLog = ''
outDir = ''
strSearchTime = ""
dateSearch = []                 # [year, month, day, hour]
days = 0

try:
    opts, args = getopt.getopt(
            sys.argv[1:],
            'i:t:d:',
            ["inp=","time=","days="])
except getopt.GetoptError:
    printHlpFull()              # print full help
    sys.exit(2)

nArg = 0
for opt, arg in opts:
    if opt == '-h':
        printHlpFull()              # print full help
        sys.exit()
    elif opt in ("-i", "--inp"):
        inpZipIgraLog = arg
        nArg = nArg + 1
    elif opt in ("-t", "--time"):
        strSearchTime = arg.strip('"')
        nArg = nArg + 1
    elif opt in ("-d", "--days"):
        days = int(arg)
        # print('n. days: {}'.format(days))
        nArg = nArg + 1

if nArg < 3:
    printHlpFull()              # print full help
    sys.exit()

# -------------------------------------------------------------------------
# fields of dateSearch
dateSearch.append(strSearchTime[0:4])           # year
dateSearch.append(strSearchTime[5:7])           # month
dateSearch.append(strSearchTime[8:10])          # day
dateSearch.append(strSearchTime[11:13])         # hour
dateSearch.append(strSearchTime[14:16])         # minutes

strDateSearch = ""
for i in range(0, 5):
    strDateSearch += dateSearch[i]
print("dateSearch: [{}][{}]".format(dateSearch, strDateSearch))

# format Date in human format
strDateHuman = ""
strDateHuman += dateSearch[0]
for i in range(0, 3):
    strDateHuman += "/"
    strDateHuman += dateSearch[i]
strDateHuman += " " + dateSearch[3]
strDateHuman += ":" + dateSearch[4]

# -------------------------------------------------------------------------

fpZipIgraLog    = get_full_path(inpZipIgraLog)     # full path zip
dirZipIgraLog   = get_dir_name(fpZipIgraLog)       # directory zip 
nameZipIgraLog  = get_file_name(fpZipIgraLog)      # file name
stationID = nameZipIgraLog[0:11]

# get file name index igra 
fNameIdxIgraLog  = nameZipIgraLog + '.idx'
fpIdxIgraLog     = os.path.join(dirZipIgraLog, fNameIdxIgraLog)
print("nameZipIgraLog[{}][{}]".format(nameZipIgraLog, stationID))
print("fpIdxIgraLog[{}]".format(fpIdxIgraLog))

outDir = dirZipIgraLog

with ZipFile(fpZipIgraLog, 'r') as zipObj:
   # Extract all the contents of zip file in outDir
   zipObj.extractall(outDir)

# -------------------------------------------------------------------------
print("create index ...")
igraDrvdCreateIndex(dirZipIgraLog, stationID)

# get index file
print("... read file indice")
idxLog = pd.read_csv(fpIdxIgraLog, sep = csv_sep)
print("... end read indice")

print("start search time in log ...")

search_time = dateSearch[0]
search_time += '-' + dateSearch[1]
search_time += '-' + dateSearch[2]
search_time += ' ' + dateSearch[3]
search_time += ':' + dateSearch[4] + ':00'
print("search_time: [{}]".format(search_time))
                               
# -------------------------------------------------------------------------
# calcola i limiti dei tempi
# convert start time in epochtime
tmUtc_search = time.strptime(search_time, "%Y-%m-%d %H:%M:%S")
search_tmEpoch = timegm(tmUtc_search)
# calculate end time in epochtime
# sum days in seconds to search_tmEpoch
endSrc_tmEpoch = search_tmEpoch + 86400 * days

# get a column with time_epoch
#### selected_columns = idxLog[["tm_epoch"]]
#### dfSearch["tm_epoch"] = selected_columns.copy()
#### dfSearch["tm_epoch"] = dfSearch["tm_epoch"] - search_tmEpoch

# https://stackoverflow.com/questions/37761238/how-do-i-select-and-store-columns-greater-than-a-number-in-pandas
# see example:
# Minimum (for the b column) for the rows satisfying b > 10 condition
# df.loc[df.b > 10, 'b'].min()
# https://community.dataquest.io/t/pandas-return-row-with-the-maximum-value-of-a-column/258474
# example:
# df.iloc[df['column_name'].idxmax()]
# idxmax() will return the index position of the row with the highest value.
# Then you can use iloc to return the row with that index.
# WARNING: If there are multiple max values this method will only return the first row with the max value.
#

min_val = idxLog.loc[(search_tmEpoch >= idxLog.tm_epoch), 'tm_epoch'].max()
#
max_val = idxLog.loc[(endSrc_tmEpoch >= idxLog.tm_epoch), 'tm_epoch'].max()

delta_sec = search_tmEpoch - min_val

# get all rows from min_val and max_val
risIdx = idxLog[(idxLog['tm_epoch']>=min_val ) & (idxLog['tm_epoch']<=max_val)]

print(risIdx)
print("... end search in log")

# reset index and get data
risIdx.reset_index(drop=True, inplace=True)

# -------------------------------------------------------------------------
# https://stackoverflow.com/questions/15943769/how-do-i-get-the-row-count-of-a-pandas-dataframe
nRows_risIdx = risIdx.shape[0]  # gives number of row count
print("n. righe risIdx: {}".format(nRows_risIdx))

n_rec = risIdx.at[0, 'n_rec']
pos_data = risIdx.at[0, 'pos_data']         # start position in file

# ---------------------------------------
delta_hour = int(delta_sec / 3600)
delta_day = delta_hour / 24
print("Differenza di tempo in ore: {}".format(delta_hour))
if delta_day >= 1:
    printf("Warning: il record radiosonda e' stato acquisito da {} giorni rispetto l'orario fornito in ingresso".format(delta_day)) 

# ---------------------------------------

if n_rec == 0:
    print("No record to analyze")
    sys.exit()

fNameIgraLog = get_file_name(fpZipIgraLog)
fNameIgraLog += '.txt'
fpIgraLog = os.path.join(dirZipIgraLog, fNameIgraLog)
print(fpIgraLog)

# --------------------------------------------------------------------------------------
# get inputstation, create report file names

inputstation = stationID.upper()        # esempio: TSM00060760

# html report file from station
str_days = str(days).zfill(3)
HtmlRep_N_Height = "reNH-{}-{}-{}days.html".format(inputstation, strDateSearch, str_days)
HtmlRep_M_Height = "reMH-{}-{}-{}days.html".format(inputstation, strDateSearch, str_days)
HtmlRep_N_slope  = "slNH-{}-{}-{}days.html".format(inputstation, strDateSearch, str_days)
HtmlRep_M_slope  = "slMH-{}-{}-{}days.html".format(inputstation, strDateSearch, str_days)

# full path file name html report
fpHtmlRep_N_Height = os.path.join(dirZipIgraLog, HtmlRep_N_Height)
fpHtmlRep_M_Height = os.path.join(dirZipIgraLog, HtmlRep_M_Height)
fpHtmlRep_N_slope  = os.path.join(dirZipIgraLog, HtmlRep_N_slope)
fpHtmlRep_M_slope  = os.path.join(dirZipIgraLog, HtmlRep_M_slope)

keySearch = "#" + inputstation                              # search string
idxKey = 0
keySearch += " " + dateSearch[idxKey]                       # add time field
print(keySearch)

# ---------------------------------------------------------------
# see documentation:
# ftp://ftp.ncdc.noaa.gov/pub/data/igra/igra2-dataset-description.docx
# ftp://ftp.ncdc.noaa.gov/pub/data/igra/derived/igra2-derived-format.txt
# -------------------------------
# Variable        Columns Type  
# -------------------------------
# PRESS           1-  7   Integer
# REPGPH          9- 15   Integer   reported geopotential height (meters).
# CALCGPH        17- 23   Integer   calculated geopotential height (meters)
# TEMP           25- 31   Integer
# TEMPGRAD       33- 39   Integer
# PTEMP          41- 47   Integer
# PTEMPGRAD      49- 55   Integer
# VTEMP          57- 63   Integer
# VPTEMP         65- 71   Integer
# VAPPRESS       73- 79   Integer
# SATVAP         81- 87   Integer
# REPRH          89- 95   Integer
# CALCRH         97-103   Integer
# RHGRAD        105-111   Integer
# UWND          113-119   Integer
# UWDGRAD       121-127   Integer
# VWND          129-135   Integer
# VWNDGRAD      137-143   Integer
# N             145-151   Integer   the refractive index (unitless).
# -------------------------------
# 
# Notes:
# REPGPH 	reported geopotential height (meters). 
#         This value is often not available at significant levels.
# 		
# CALCGPH calculated geopotential height (meters). 
#         The geopotential height has been estimated by applying the hydrostatic balance to
# 		the atmospheric layer between the next lower level with a reported geopotential height and the current level.

# https://stackoverflow.com/questions/41386443/create-pandas-dataframe-from-txt-file-with-specific-pattern

# CalcGph   : calculated geopotential height (meters)
# RefIndex  : the refractive index (unitless).

height_limit = 4000             # max height for analysis

# list of graph traces
grTrace_N_HGHT = []             # traces x:'N', y:'HGHT'
grTrace_M_HGHT = []             # traces x:'M', y:'HGHT'
grTrace_HGHT_SLOPE_N_H = []     # traces x:'HGHT', y:'slopeN_H'
grTrace_HGHT_SLOPE_M_H = []     # traces x:'HGHT', y:'slopeM_H'

# ---------------------------------------------------------------

# per ogni riga del dataframe risIdx, genera i file csv dei report
Item = namedtuple('CalcGph', 'RefIndex')
for rowPos in range(nRows_risIdx):
    items = []                                          # launch acquisition data
    date_launch = risIdx.at[rowPos, 'date']             # date/time launch radiosonda
    pos_data = risIdx.at[rowPos, 'pos_data']            # start position in file log

    # form filename of output csv file
    fNameOutCsv = stationID + "-"
    fNameOutCsv += time_compact(date_launch)
    fNameOutCsv += '.csv'
    fpOutCsv = os.path.join(dirZipIgraLog, fNameOutCsv)
    print(fpOutCsv)

    with open(fpIgraLog,'r') as rsLog:
        rsLog.seek(pos_data, os.SEEK_SET)  # go to the beginning of the file displacement pos_data.
        while True:
            line = rsLog.readline().rstrip()
            if not line:
                # eof
                break
            if line.startswith('#'):
                # new record
                break
            # insert data in dataframe
            CalcGph     = int(line[16:23])              # calculated geopotential height (meters)
            RefIndex    = int(line[144:151])            # N, the refractive index (unitless)
            items.append((CalcGph, RefIndex))
            # check if CalcGph is greater than height_limit
            if CalcGph > height_limit:
                # acquisition limit, based on height
                break
    rsLog.close()

    # sys.exit()

    # --------------------------------------------------------------------------------------

    # create dataframe 
    dtAcq02 = pd.DataFrame.from_records(items, columns=['HGHT', 'N'])
    # dataframe columns:
    # HGHT  : altezza (m) (used: CALCGPH calculated geopotential height (m))
    # N     : the refractive index (unitless)

    # --------------------------------------------------------------------------------------
    # calculate dtAcq02['M'] = dtAcq02['N'] + 0.157 * dtAcq02['HGHT']
    dtAcq02['M'] = dtAcq02.N + 0.157 * dtAcq02.HGHT

    # --------------------------------------------------------------------------------------
    # calculate difference of 'N' and 'HGHT' columns

    # Calculates the difference of a DataFrame element compared with another element in the DataFrame 
    # (default is the element in the same column of the previous row).
    dtAcq02['deltaN'] = dtAcq02['N'].diff()
    dtAcq02['deltaM'] = dtAcq02['M'].diff()

    dtAcq02['deltaH'] = dtAcq02['HGHT'].diff()

    # calc dtAcq02['deltaH']/dtAcq02['deltaN']
    dtAcq02['slopeN_H'] = dtAcq02['deltaN'].div(dtAcq02['deltaH'])
    # calc dtAcq02['deltaH']/dtAcq02['deltaM']
    dtAcq02['slopeM_H'] = dtAcq02['deltaM'].div(dtAcq02['deltaH'])

    # Access a group of rows and columns by label(s) or a boolean array.
    dtAcq02.loc[~np.isfinite(dtAcq02['slopeN_H']), 'slopeN_H'] = np.nan
    dtAcq02.loc[~np.isfinite(dtAcq02['slopeM_H']), 'slopeM_H'] = np.nan

    # note: slopeN_H must be divided by 1000. For this parameter the height is in km
    dtAcq02['slopeN_H'] = dtAcq02.slopeN_H * 1000
    dtAcq02['slopeM_H'] = dtAcq02.slopeM_H * 1000

    # Drop the rows even with single NaN or single missing values.
    dtAcq02 = dtAcq02.dropna()

    print(dtAcq02)
    dtAcq02.to_csv(fpOutCsv, header=True, index=True, sep=csv_sep)

    # ---------------------------------------------------------
    # save traces in lists

    # traces x:'N', y:'HGHT'
    grTrace_N_HGHT.append(
        go.Scatter(
            x=dtAcq02['N'], y=dtAcq02['HGHT'],
            # line=dict(width=3,color='green'),
            line=dict(width=3),
            name=date_launch
        )
    )
    # traces x:'M', y:'HGHT'
    grTrace_M_HGHT.append(
        go.Scatter(
            x=dtAcq02['M'], y=dtAcq02['HGHT'],
            # line=dict(width=3,color='green'),
            line=dict(width=3),
            name=date_launch
        )
    )
    # dtAcq02['HGHT'] in km
    dtAcq02.HGHT = dtAcq02['HGHT'] / 1000
    # traces x:'HGHT', y:'slopeN_H'
    grTrace_HGHT_SLOPE_N_H.append(     
        go.Scatter(
            x=dtAcq02['HGHT'], y=dtAcq02['slopeN_H'],
            # line=dict(width=3,color='green'),
            line=dict(width=3),                
            name=date_launch
        )
    )
    # traces x:'HGHT', y:'slopeM_H'
    grTrace_HGHT_SLOPE_M_H.append(     
        go.Scatter(
            x=dtAcq02['HGHT'], y=dtAcq02['slopeM_H'],
            # line=dict(width=3,color='green'),
            line=dict(width=3),                
            name=date_launch
        )
    )
    
    # ---------------------------------------------------------
    # free memory
    # delete dataframes
    # example:
    # This will delete the dataframe and will release the RAM/memory
    # del [[df_1,df_2]]
    # gc.collect()
    # df_1=pd.DataFrame()
    # df_2=pd.DataFrame()
    
    del items
    del [[dtAcq02]]
    gc.collect()                # garbage collection
    ## ------------------------- end for rowPos in range(nRows_risIdx)

# --------------------------------------------------------------------------------------
# GRAPHS OUTPUT
# --------------------------------------------------------------------------------------
# https://plotly.com/python/v3/figure-labels/
# for symbols, see:
# https://www.w3schools.com/html/html_symbols.asp

fig = go.Figure()

# -------------- COMMON DATA

# name_graph = "Station: " + inputstation + "      Date: " + str(inputyear) + "/" + str(inputmonth) + "/" + str(inputday) + " " + str(inputhour) + ":00"
name_graph = "Station: " + inputstation + "<br>Start date: " + strDateHuman

# default font parameters
def_font=dict(
    family='Arial, monospace',
    size=16,
    color="#000000"                 # black
)

def_tickfont = dict(
        size = 16,
        color = "#000000"               # black
),        

# mod 19/05
EnableGraph = False

if EnableGraph:
    # --------------------------------------------------[ grafici da non generare]

    # -------------- create graph HEIGHT / N
    GraphLayout = go.Layout(
        title=go.layout.Title(
            text='<b>' + name_graph + '</b>',       # bold
            font=dict(
                family='Arial, monospace',
                size=16,
                color="#000000"                 # black
            ),
            xref='paper',
            x=0
        ),
        xaxis=go.layout.XAxis(                           
            tickfont = dict(
                    size = 16,
                    color = "#000000"               # black
            ),        
            title=go.layout.xaxis.Title(
                text='N',
                font=dict(
                    family='Arial, monospace',
                    size=16,
                    color="#000000"                 # black
                )
            )
        ),
        yaxis=go.layout.YAxis(
            range=[0, height_limit],
            tickfont = dict(
                    size = 16,
                    color = "#000000"               # black
            ),        
            title=go.layout.yaxis.Title(
                text='Height (m)',
                font=dict(
                    family='Arial, monospace',
                    size=16,
                    color="#000000"                 # black
                )
            )
        )
    )
    fig = go.Figure(data=grTrace_N_HGHT, layout=GraphLayout)
    fig.write_html(fpHtmlRep_N_Height, auto_open=False)

    # -------------- create graph HEIGHT / M
    GraphLayout = go.Layout(
        title=go.layout.Title(
            text='<b>' + name_graph + '</b>',       # bold
            font=dict(
                family='Arial, monospace',
                size=16,
                color="#000000"                 # black
            ),
            xref='paper',
            x=0
        ),
        xaxis=go.layout.XAxis(
            tickfont = dict(
                    size = 16,
                    color = "#000000"               # black
            ),        
            title=go.layout.xaxis.Title(
                text='M',
                font=dict(
                    family='Arial, monospace',
                    size=16,
                    color="#000000"                 # black
                )
            )
        ),
        yaxis=go.layout.YAxis(
            range=[0, height_limit],
            tickfont = dict(
                    size = 16,
                    color = "#000000"               # black
            ),        
            title=go.layout.yaxis.Title(
                text='Height (m)',
                font=dict(
                    family='Arial, monospace',
                    size=16,
                    color="#000000"                 # black
                )
            )
        )
    )
    fig = go.Figure(data=grTrace_M_HGHT, layout=GraphLayout)
    fig.write_html(fpHtmlRep_M_Height, auto_open=False)
    # --------------------------------------------------[ end grafici da non generare]

# -------------- create graph slope N - H
GraphLayout = go.Layout(
    title=go.layout.Title(
        text='<b>' + name_graph + '</b>',       # bold
        font=dict(
            family='Arial, monospace',
            size=16,
            color="#000000"                 # black
        ),
        xref='paper',
        x=0
    ),
    xaxis=go.layout.XAxis(
        range=[0, 4],
        tickfont = dict(
                size = 16,
                color = "#000000"               # black
        ),        
        title=go.layout.xaxis.Title(
            text='<b>Height (km)</b>',
            font=dict(
                family='Arial, monospace',
                size=16,
                color="#000000"                 # black
            )
        )
    ),
    yaxis=go.layout.YAxis(
        tickfont = dict(
                size = 16,
                color = "#000000"               # black
        ),        
        title=go.layout.yaxis.Title(
            text='<b>&#916;N/&#916;H, km<sup>-1</sup></b>',
            font=dict(
                family='Arial, monospace',
                size=16,
                color="#000000"                 # black
            )
        )
    )
)

fig = go.Figure(data=grTrace_HGHT_SLOPE_N_H, layout=GraphLayout)

fig.update_layout(plot_bgcolor='rgb(255,255,255)')
fig.update_xaxes(showgrid=True,gridwidth=1, gridcolor='LightPink',showline=True, linewidth=1, linecolor='black', mirror=True)
fig.update_yaxes(showgrid=True,gridwidth=1, gridcolor='LightPink',showline=True, linewidth=1, linecolor='black', mirror=True)
fig.update_layout()

fig.write_html(fpHtmlRep_N_slope, auto_open=False)

# -------------- create graph slope M - H
GraphLayout = go.Layout(
    title=go.layout.Title(
        text='<b>' + name_graph + '</b>',       # bold
        font=dict(
            family='Arial, monospace',
            size=16,
            color="#000000"                 # black
        ),
        xref='paper',
        x=0
    ),
    xaxis=go.layout.XAxis(
        range=[0, 4],
        tickfont = dict(
                size = 16,
                color = "#000000"               # black
        ),        
        title=go.layout.xaxis.Title(
            text='<b>Height (km)</b>',
            font=dict(
                family='Arial, monospace',
                size=16,
                color="#000000"                 # black
            )
        )
    ),
    yaxis=go.layout.YAxis(
        tickfont = dict(
                size = 16,
                color = "#000000"               # black
        ),        
        title=go.layout.yaxis.Title(
            text='<b>&#916;M/&#916;H, km<sup>-1</sup></b>',
            font=dict(
                family='Arial, monospace',
                size=16,
                color="#000000"                 # black
            )
        )
    )
)

fig = go.Figure(data=grTrace_HGHT_SLOPE_M_H, layout=GraphLayout)

fig.update_layout(plot_bgcolor='rgb(255,255,255)')
fig.update_xaxes(showgrid=True,gridwidth=1, gridcolor='LightPink',showline=True, linewidth=1, linecolor='black', mirror=True)
fig.update_yaxes(showgrid=True,gridwidth=1, gridcolor='LightPink',showline=True, linewidth=1, linecolor='black', mirror=True)
fig.update_layout()

fig.write_html(fpHtmlRep_M_slope, auto_open=False)



