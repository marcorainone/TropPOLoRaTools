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
# The program filters the ttnmapper reports and prepares them for subsequent processing. Receives:
# 1. ttnmapper report file
# 2. minimum distance of the device from the gateway in km, to filter the closest gateways
# 3. a flag to take into account the upper / lower case letters in the gateway name
# 4. output directory of the generated report in csv format
# ----------------------------------------------------------------

import os
import os.path
import getopt, sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from staticmap import StaticMap, CircleMarker
import csv, json, sys
import geopy.distance
from array import *

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
    print('{} -i <TTN Mapper Log file> -d <min distance device to gateway (km)> -c <TTN gtw ID> -o <out dir>'.format(sys.argv[0]))

def printHlpFull():
    print('{} -i <TTN Mapper Log file> -d <min distance device to gateway (km)> -c <TTN gtw ID> -o <out dir>'.format(sys.argv[0]))
    print('Example:')
    print('{} -i rfsee_drivetest_unit_4.txt -d 20 -c \"no\" -o \"./outdir\"'.format(sys.argv[0]))
    print('Read rfsee_drivetest_unit_4.txt. Remove positions with distance less than 20 km'.format(sys.argv[0]))
    print('If -c \"no\", ignore letter case of gateway id name for search')
    print('Store csv result file in ./output directory')


# -------------------------------------------------------------------------
# Get command-line arguments

# initialize variables
inpTTNMapperLog = ''
outDirCsv = ''
minDist = 20
flCaseGtwId = True

try:
    opts, args = getopt.getopt(
            sys.argv[1:],
            'i:d:c:o:',
            ["inp=","dist=","case=","out="])
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
    elif opt in ("-i", "--inp"):
        inpTTNMapperLog = arg
        # print('TTN Mapper Log file: {}'.format(inpTTNMapperLog))
        nArg = nArg + 1
    elif opt in ("-o", "--out"):
        outDirCsv = arg
        # print('Output directory csv result: {}'.format(outDirCsv))
        nArg = nArg + 1
    elif opt in ("-d", "--dist"):
        minDist = int(arg)
        # print('min distance: {}'.format(minDist))
        nArg = nArg + 1
    elif opt in ("-c", "--case"):
        flCaseGtwId = False;
        # print(arg)
        if str2bool(arg):
            flCaseGtwId = True;
        # print('In TTN gateway name search, check case of letters: {}'.format(flCaseGtwId))
        nArg = nArg + 1

# print(nArg)
        
if nArg < 4:
    printHlpFull()              # print full help
    sys.exit()

## if not os.path.exists(outDirCsv):
##     os.makedirs(outDirCsv)

# ---------------------------------------------------------------
# in base of inpTTNMapperLog, get file name and extension
# full path inpTTNMapperLog
# original
# fpTTNMapperLog = os.path.join(PathBaseDir, inpTTNMapperLog)

# convert file path to absolute
fpTTNMapperLog = get_full_path(inpTTNMapperLog)

# get filename of output file
outCsv = get_file_name(inpTTNMapperLog) + '.csv'
# full path output dir
if not os.path.exists(outDirCsv):
    os.mkdir(outDirCsv, access_rights)
fpOutDir = get_full_path(outDirCsv)     # full path output dir

# full path output file
fpOutCsv = os.path.join(fpOutDir, outCsv)

# ---------------------------------------------------------------
# read TTN gateways position from csv
fp_TTN_gateways_csv = os.path.join(PathBaseDir, "gtwttn-EU_863_870.csv")
gtw = pd.read_csv(fp_TTN_gateways_csv, sep = csv_sep)

# ---------------------------------------------------------------
# read the file from TTNMapper and clean up the elements
data = pd.read_csv(fpTTNMapperLog, skipinitialspace = True)
data.columns = data.columns.str.replace(' ', '')            # Togli spazi dal nome delle colonne
#remove useless columns
delete_columns = ['id', 'appeui', 'modulation', 'freq', 'accuracy', 'hdop', 'sats', 'provider', 'user_agent']
data.drop(columns=delete_columns, axis=1, inplace=True)

data = data.dropna()                                        # drop all rows with any NaN and NaT values
## print(data)

# trova quanti gateways ha raggiunto in tutto
gateways = data.gwaddr.unique()

# rimuovi spazi dai nomi dei gateways
gateways = [x.strip(' ') for x in gateways]
# print(gateways)

# sys.exit()

# add 2 new columns: lat, lon of gateway. Initialize with nan
data['gtw_lat'] = np.NaN
data['gtw_lon'] = np.NaN 

# aggiungi due colonne con lat e lon dei gateways
for x in range(0, len(gateways)):
    df_gtw = gtw[gtw.gtw_id.str.contains(gateways[x], case=flCaseGtwId, regex=False)]
    if df_gtw.empty:
        continue

    # ----------------- print("IN  gw[{}]".format(gateways[x]))
    df_gtw.reset_index(drop=True, inplace=True)

    ## print(df_gtw)
    
    lat = df_gtw.at[0,'lat']
    lon = df_gtw.at[0,'lon']
    
    # sys.exit()
    
    data.loc[data.gwaddr.str.contains(gateways[x], regex=False) , 'gtw_lat'] = lat
    data.loc[data.gwaddr.str.contains(gateways[x], regex=False) , 'gtw_lon'] = lon

# Drop rows with NaN in specific columns. here we are removing Missing values in columns
# data = data.dropna(subset=['gtw_lat', 'gtw_lon'])
data = data.dropna()
# print(data)

# specify pandas to not to keep the original index with the argument drop=True.
data.reset_index(drop=True, inplace=True)

# add column with distance
data['distance'] = np.NaN

# iterate through each row and calculate 'distance'  
for ind in data.index: 
    coords_1 = (data['lat'][ind], data['lon'][ind])
    coords_2 = (data['gtw_lat'][ind], data['gtw_lon'][ind])
    distance=geopy.distance.geodesic(coords_1, coords_2).km
    # print(distance)
    if distance <= minDist:
        # distance less than limit
        continue
    data.at[ind, 'distance'] = int(distance)
    
# Drop rows with NaN in specific columns. here we are removing Missing values in columns
data = data.dropna()
# print(data)
data.reset_index(drop=True, inplace=True)

# distance: set all values integer 
data['distance'] = data['distance'].apply(np.int64)
# all coordinates with 4 decimals:
# see: https://www.geeksforgeeks.org/python-pandas-dataframe-round/
data = data.round({'lat':4, 'lon':4, 'gtw_lat':4, 'gtw_lon':4})

# ---------------------------------------------------------------
# remove columns: ['alt','datarate','snr','rssi']
delete_columns = ['alt','datarate','snr','rssi']
data.drop(columns=delete_columns, axis=1, inplace=True)

# ---------------------------------------------------------------
# reorder columns: ['nodeaddr','lat','lon','gwaddr','gtw_lat','gtw_lon','distance','time']
# column_names = ['nodeaddr','lat','lon','gwaddr','gtw_lat','gtw_lon','distance','time']
column_names = ['time','distance','nodeaddr','lat','lon','gwaddr','gtw_lat','gtw_lon']
data = data.reindex(columns=column_names)

## print(data)
# ---------------------------------------------------------------
# sort dataframe
# sorting data frame by columns:
# ['time','nodeaddr','gwaddr','distance']
data.sort_values(['distance','time','nodeaddr','gwaddr'], axis=0, 
        ascending=[False,True,True,True], inplace=True)
data.reset_index(drop=True, inplace=True)
print(data)

# ---------------------------------------------------------------
# save to csv these columns:
data.to_csv(fpOutCsv, sep= csv_sep, encoding='utf-8', index=False)
                 
