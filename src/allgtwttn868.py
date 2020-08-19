#!/usr/bin/python3
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
# Generate csv file of EU_863_870 TTN gateways
# ----------------------------------------------------------------
#
import os
import wget
import json

# https://github.com/TheThingsNetwork/lorawan-frequency-plans
# The Things Network Stack supports at least the following bands            
# AS_923             Asia 923 MHz
# AU_915_928         Australia 915 - 928 MHz
# CN_470_510         China 470 - 510 MHz
# CN_779_787         China 779 - 787 MHz
# EU_433             Europe 433 MHz
# EU_863_870         Europe 863 - 870 MHz
# IN_865_870         India 865 - 867 MHz
# KR_920_923         Korea 920 - 923 MHz
# RU_864_870         Russia 864 - 870 MHz
# US_902_928         United States 902 - 928 MHz

# ---------------------------------------------------------------
# config
#
PathBaseDir = os.getcwd()               # current working directory of the process
csv_sep = ';'                           # char separator for csv

# ---------------------------------------------------------------
# get gateway list from ttn
#
fp_TTN_all_gateways = os.path.join(PathBaseDir, "TTNgateways.json")

# https://stackoverflow.com/questions/7243750/download-file-from-web-in-python-3
# https://stackabuse.com/download-files-with-python/
url = 'http://noc.thethingsnetwork.org:8085/api/v2/gateways'
# response = urllib.request.urlopen(url)
# data = response.read()      # a `bytes` object
wget.download(url, fp_TTN_all_gateways)

# ---------------------------------------------------------------
# https://stackoverflow.com/questions/36606930/delete-an-element-in-a-json-object

# Transform input file of json list to python objects
#
with open(fp_TTN_all_gateways, 'r') as data_file:
    data = json.load(data_file)

# ---------------------------------------------------------------
# remove elements not used
# for element in data['statuses']:
#
for key,val in list(data['statuses'].items()):
    # print(key)                # print gateway id
    # ---------------- check frequency_plan
    if "frequency_plan" not in val:
        # there is no frequency_plan
        data['statuses'].pop(key)
        continue
    # check if frequency_plan different of "EU_863_870"
    if val["frequency_plan"] != "EU_863_870":
        # frequency_plan different to EU_863_870
        data['statuses'].pop(key)
        continue
    # check location data
    # if (len(val['location']) == 0):
    if 'location' not in val:
        # ---------------- empty coordinates
        data['statuses'].pop(key)
        continue
    # ---------------- check latitudes
    if "latitude" not in val['location']:
        # there is no latitude
        data['statuses'].pop(key)
        continue
    # ---------------- check latitudes
    if "longitude" not in val['location']:
        # there is no longitude
        data['statuses'].pop(key)
        continue
    
    # print(val)
    val.pop('timestamp', None)
    val.pop('authenticated', None)
    val.pop('uplink', None)
    val.pop('downlink', None)
    val.pop('gps', None)
    val['location'].pop('source', None)
    val.pop('time', None)
    val.pop('rx_ok', None)
    val.pop('tx_in', None)

# ---------------------------------------------------------------
# form file csv
#
fp_TTN_gateways_csv = os.path.join(PathBaseDir, "gtwttn-EU_863_870.csv")

with open(fp_TTN_gateways_csv, 'w') as gtwList_csv:
    # first row
    line = "\"{}\"{}".format(
            "gtw_id", csv_sep)
    line += "\"{}\"{}\"{}\"{}".format(
            "lat", csv_sep,
            "lon", csv_sep)
    line += "\"{}\"\n".format(
            "alt")
    gtwList_csv.write(line)
    
    for key,val in list(data['statuses'].items()):
        # form string
        # id, frequency_plan
        line = "\"{}\"{}".format(
                key, csv_sep)
        # lat, lon
        line += "{}{}{}{}".format(
                val['location']['latitude'], csv_sep,
                val['location']['longitude'], csv_sep)
        # altitude
        if "altitude" in val['location']:
            line += "{}".format(
                 val['location']['altitude'])
        line += "\n"                 
        gtwList_csv.write(line)
    gtwList_csv.close()