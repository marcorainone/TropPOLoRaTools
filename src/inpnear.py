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
# Auxiliary program, used to create a csv file compatible with the rsigra-near.py format. 
# In this case the data is entered manually.
# The command can be used to create a csv file to be analyzed with subsequent trope tools.

import sys

import os
import os.path
import getopt, sys
import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from staticmap import StaticMap, CircleMarker
import csv, json, sys
import geopy.distance
from array import *

import ftplib

# ---------------------------
# constant limits
maxInt   = sys.maxsize
minInt   = -sys.maxsize-1
maxFloat = sys.float_info.max
minFloat = sys.float_info.min

# ---------------------------------------------------------------
# config
#
PathBaseDir = os.getcwd()               # current working directory of the process
access_rights = 0o777                   # define the access rights file/folder
csv_sep = ';'                           # char separator for csv


# -----------------------------------------------------------------------------------
# input parameters

# input string
def inputString(message):
    ok = False
    while not ok:
        try:
            inp = input(message + " ? ")
        except KeyboardInterrupt:
            sys.exit(0)
        print("  Input: [{}]".format(inp), end="")
        try:
            ris = input(" OK (y/n) ? ").lower()
        except KeyboardInterrupt:
            sys.exit(0)
        if ris == 'y':
            ok = True
    return(inp)

def inputInt(message, fChkLimits, min, max):
    ok = False
    if fChkLimits:
        msg = "{} ({},{}) ? ".format(message, min, max)
    else:
        msg = "{} ? ".format(message)
    
    while not ok:
        # print without newline
        try:
            print(msg, end="")
            inp = int( input() )
        except KeyboardInterrupt:
            sys.exit(0)
        except:
            print("Error")
            continue
        if fChkLimits:
            # check range
            if (min > inp):
                print("Error: {} less than min ({})".format(inp, min))
                continue
            elif (inp > max):
                print("Error: {} greater than max ({})".format(inp, max))
                continue
        print("  Input: [{}]".format(inp), end="")
        try:
            ris = input(" OK (y/n) ? ").lower()
        except KeyboardInterrupt:
            sys.exit(0)
        if ris == 'y':
            ok = True
    return(inp)

def inputFloat(message, fChkLimits, min, max):
    ok = False
    if fChkLimits:
        msg = "{} ({},{}) ? ".format(message, min, max)
    else:
        msg = "{} ? ".format(message)
    
    while not ok:
        # print without newline
        try:
            print(msg, end="")
            inp = float( input() )
        except KeyboardInterrupt:
            sys.exit(0)
        except:
            print("Error")
            continue
        if fChkLimits:
            # check range
            if (min > inp):
                print("Error: {} less than min ({})".format(inp, min))
                continue
            elif (inp > max):
                print("Error: {} greater than max ({})".format(inp, max))
                continue
        print("  Input: [{}]".format(inp), end="")
        try:
            ris = input(" OK (y/n) ? ").lower()
        except KeyboardInterrupt:
            sys.exit(0)
        if ris == 'y':
            ok = True
    return(inp)

# get latitude, longitude
def inputPosition(message):
    ok = False
    while not ok:
        # print without newline
        try:
            print("{} coordinates (latitude and longitude in degrees, ex: 45.6573 13.7694):".format(message))
            lat,lon = map(float, input(" ? ").split())
        except KeyboardInterrupt:
            sys.exit(0)
        except:
            print("Error")
            continue
        # The valid range of latitude in degrees is -90 and +90 
        # Longitude is in the range -180 and +180
        if not (-90.0 <= lat <= 90.0):
            print("latitude: {} not in range (-90, +90) degrees".format(lat))
            continue
        if not (-180.0 <= lon <= +180.0):
            print("longitude: {} not in range (-180, +180) degrees".format(lon))
            continue
        print("  Coordinates: [{}, {}]".format(lat, lon), end="")
        try:
            ris = input(" OK (y/n) ? ").lower()
        except KeyboardInterrupt:
            sys.exit(0)
        if ris == 'y':
            ok = True
    print("Coordinates: [{}, {}]".format(lat, lon))
    return(lat, lon)

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

# https://stackoverflow.com/questions/541390/extracting-extension-from-filename-in-python
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
    print('{} -o <path output csv>>'.format(sys.argv[0]))

def printHlpFull():
    print('{} -o <path output csv>>'.format(sys.argv[0]))
    print('Example:')
    print('{} -o ./data/result.csv'.format(sys.argv[0]))
    print('Store result data in ./data/result.csv file')

# -----------------------------------------------------------------------------------
# main

# Get command-line arguments

# initialize variables
inpEventsLog = ''
outDirCsv = ''

try:
    opts, args = getopt.getopt(
            sys.argv[1:],
            'o:',
            ["out="])
except getopt.GetoptError:
    printHlpFull()              # print full help
    sys.exit(2)

nArg = 0
# print(opts)
# print(args)
for opt, arg in opts:
    if opt == '-h':
        printHlpFull()              # print full help
        sys.exit()
    elif opt in ("-o", "--out"):
        inpEventsLog = arg
        # print('TTN Mapper Log file: {}'.format(inpTTNEventsLog))
        nArg = nArg + 1

# print(nArg)
        
if nArg < 1:
    printHlpFull()              # print full help
    sys.exit()

# ---------------------------------------------------------------

# file name of radiosonde list
LstFile = "igra2-station-list.txt"
fpLstFile = os.path.join(PathBaseDir, LstFile)

# get filename of output file
outCsv = get_file_name(inpEventsLog) + '.csv'
# full path output dir
outDirCsv = get_dir_name(inpEventsLog)
if not os.path.exists(outDirCsv):
    os.mkdir(outDirCsv, access_rights)
fpOutDir = get_full_path(outDirCsv)     # full path output dir
# full path output file
fpOutCsv = os.path.join(fpOutDir, outCsv)

# input data for csv with near radiosonda
# csv parameters:
# ;time;distance;nodeaddr;lat;lon;gwaddr;gtw_lat;gtw_lon;rs_id;rs_lat;rs_lon;rs_distance
# example:
# 0;2020-03-25 09:52:55;4858;rfsee_drivetest_unit_4;52.0894;5.1035;008000000000A889;10.0;20.0;TSM00060760;33.9167;8.1667;520

data = pd.DataFrame(columns = ['time', 'distance', 'nodeaddr', 'lat', 'lon', 'gwaddr', 'gtw_lat', 'gtw_lon', 'rs_id', 'rs_lat', 'rs_lon', 'rs_distance'])

# time:
data.at[0, 'time'] = inputString("time (year-month-day hour:min:sec Example: 2020-03-25 09:52:55)")
# distance:
# nodeaddr:
data.at[0, 'nodeaddr'] = inputString("node ID string")
# lat:
# lon:
data.at[0, 'lat'], data.at[0, 'lon'] = inputPosition("Node position")
# gwaddr:
data.at[0, 'gwaddr'] = inputString("gateway ID string")
# gtw_lat:
# gtw_lon:
data.at[0, 'gtw_lat'], data.at[0, 'gtw_lon'] = inputPosition("Gateway position")
# rs_id:
# rs_lat:
# rs_lon:
# rs_distance:

# calc distance
coords_1 = (data['lat'][0], data['lon'][0])
coords_2 = (data['gtw_lat'][0], data['gtw_lon'][0])
data.at[0, 'distance'] = geopy.distance.geodesic(coords_1, coords_2).km

# calculate median point of coordinates
mlat = (data['lat'][0] + data['gtw_lat'][0]) / 2.0
mlon = (data['lon'][0] + data['gtw_lon'][0]) / 2.0
coords_1 = (mlat, mlon)

# -------------------------------------------------------------------------
# read list of radiosonde
#
# with ftplib.FTP("ftp://ftp.ncdc.noaa.gov/pub/data/igra/") as ftp:
try:
    print("access to ftp://ftp.ncdc.noaa.gov/pub/data/igra ...")
    ftp = ftplib.FTP("ftp.ncdc.noaa.gov")
    ftp.login()
    ftp.cwd('pub/data/igra')              # change into "pub/data/igra" directory
    print("-------------------- ftp.ncdc.noaa.gov/pub/data/igra")
    # ftp.dir()
except:
    print("access error to ftp://ftp.ncdc.noaa.gov/pub/data/igra")
    sys.exit()
# get radiosonde list
# https://stackoverflow.com/questions/11573817/how-to-download-a-file-via-ftp-with-python-ftplib
try:
    print("get radiosonde list: {} ...".format(LstFile))
    ftp.retrbinary("RETR " + LstFile ,open(fpLstFile, 'wb').write)
except:
    print("Error download file list: {}".format(LstFile))
    sys.exit()

colIgra2Names = [
    "ICAONAT"   ,   # Character
    "NETCODE"   ,
    "IDCODE"    ,
    "IGRA2_ID"  ,   # Character
    "LATITUDE"  ,   # Real
    "LONGITUDE" ,   # Real
    "ELEVATION" ,   # Real
    "STATE"     ,   # Character
    "NAME"      ,   # Character
    "FSTYEAR"   ,   # Integer
    "LSTYEAR"   ,   # Integer
    "NOBS"      ,   # Integer
]

colIgra2StationList = [
    [ 0, 2],    # ICAONAT   : Character (Icao National Codes)
    [ 2, 3],    # NETCODE   : Character (Network Code: 
                #    I      : ICAO id (last 4 char IGRA2ID), 
                #    M      : WMO id number (last 5 char IGRA2ID),
                #    V      : Vol.Obs.id (last 5 to 6 char IGRA2ID)
                #    W      : WBAN id (last 5 char IGRA2ID)
                #    X      : Special id ("UA" with 6 alpha chr)
    [ 3,11],    # IDCODE    : Integer
    [ 0,11],    # IGRA2_ID  : Character
    [12,20],    # LATITUDE  : Real
    [21,30],    # LONGITUDE : Real
    [31,37],    # ELEVATION : Real
    [38,40],    # STATE     : Character
    [41,71],    # NAME      : Character
    [72,76],    # FSTYEAR   : Integer
    [77,81],    # LSTYEAR   : Integer
    [82,88]     # NOBS      : Integer
]

igraStation = pd.read_fwf(fpLstFile, names=colIgra2Names, header=None, colspecs=colIgra2StationList)
# igraStation.to_csv('igra2station.csv', header=True, index=True, sep=csv_sep) 
igraStation.to_csv('igra2station.csv', header=True, index=False, sep=csv_sep) 

# filter elements in list:

# get actual year
now = datetime.datetime.now()
act_year = int(now.strftime("%Y"))      # now.strftime("%Y-%m-%d %H:%M:%S")
# filter list: remove lines with LSTYEAR less than act_year
igraStation.drop(igraStation.loc[igraStation['LSTYEAR']<act_year].index, inplace=True)

# filter list: remove lines with coordinates for mobile radiosonde (see igra2-list-format.txt):
# LATITUDE   is the latitude of the station (in decimal degrees, mobile = -98.8888).
# LONGITUDE  is the longitude of the station (in decimal degrees, mobile = -998.8888).
# ELEVATION  is the elevation of the station (in meters, missing = -999.9, mobile = -998.8).
igraStation.drop(igraStation.loc[igraStation['LONGITUDE'] == -998.8888].index, inplace=True)

# reindex
igraStation.reset_index(drop=True, inplace=True)

# save for debug
igraStation.to_csv('igra2-2020.csv', header=True, index=False, sep=csv_sep) 

# initialize the last_distance to a dummy value, greather than expected
last_distance = 400000.0                    # 400000km
## print(coords_1)
for i2 in igraStation.index:
# for i2 in range(0, len(igraStation)):
    coords_2 = (igraStation['LATITUDE'][i2], igraStation['LONGITUDE'][i2])
    # print(coords_2)
    distance = geopy.distance.geodesic(coords_1, coords_2).km
    
    # set flag checking value of rs_id is not set (cell has np.NaN)
    # flSetNewRadiosonda = pd.isna(data['rs_distance'][i1])
    if last_distance > distance:
        # set new values in row
        data.at[0, 'rs_id']        = igraStation.at[i2, 'IGRA2_ID']
        data.at[0, 'rs_lat']       = igraStation.at[i2, 'LATITUDE']
        data.at[0, 'rs_lon']       = igraStation.at[i2, 'LONGITUDE'] 
        data.at[0, 'rs_distance']  = int(distance)
        last_distance = distance

radiosonde = data.rs_id.unique()

print("N. radiosonde identificate: {}".format(len(radiosonde)))
print(radiosonde)

print(data)

# ---------------------------------------------------------------
# save the new csv with radiosonda info
data.to_csv(fpOutCsv, header=True, index=True, sep=csv_sep) 
