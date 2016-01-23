from bs4 import BeautifulSoup
from optparse import OptionParser
import requests
import csv
import datetime
import time
import sys

# This script reads statistics from a VirginMedia SuperHub2 / 2ac
# It will save into a .CSV file the following information
#   * Upstream power levels
#   * Downstream power levels
#   * Downstream SNR
#   * Downstream Pre-RS Errors
#   * Downstream Post-RS Errors
# Requires http://www.crummy.com/software/BeautifulSoup/

parser = OptionParser()

parser.add_option("-c", "--channel",
                  dest="channel",
                  help="Sets the specified channel ID to return data for (must be used in conjunction with -s and -g",
                  metavar="CHANNEL")

parser.add_option("-f", "--file",
                  dest="outputfile",
                  default="vm.csv",
                  help="Sets the filename to save to (default is vm.csv)",
                  metavar="FILE")

parser.add_option("-g", "--statgroup",
                  dest="statgroup",
                  help="Sets the stat group to return data for (either ds for downstream or us for upstream)",
                  metavar="STATGROUP")

parser.add_option("-i", "--ip",
                  default="192.168.100.1",
                  dest="superhubip",
                  help="Sets the SuperHub IP Address (default is 192.168.100.1)",
                  metavar="IPADDRESS")

parser.add_option("-s", "--stat",
                  dest="stat",
                  help="Sets the statistic to return data for (must be used in conjunction with -c and -g)",
                  metavar="STAT")

parser.add_option("-t", "--stdout",
                  default=False,
                  dest="outputstdout",
                  action="store_true",
                  help="Outputs to stdout instead of a file")

options, args = parser.parse_args()

if not (options.stat is None) == (options.channel is None) == (options.statgroup is None):
    exit("The -c, -g and -s flags must either be all set, or all not set")

if not options.statgroup is None:
    if (options.statgroup != "ds") and (options.statgroup != "us"):
        exit("The -g option only accepts \"ds\" or \"us\" as valid options")

# The default SuperHub IP address.
SuperHubIP = "http://" + options.superhubip + "/"

# Fetch the HTML pages and compress whitespace
upstream = requests.get(SuperHubIP + "cgi-bin/VmRouterStatusUpstreamCfgCgi")
upstream_html = "".join(line.strip() for line in upstream.text.split("\n"))

downstream = requests.get(SuperHubIP + "cgi-bin/VmRouterStatusDownstreamCfgCgi")
downstream_html = "".join(line.strip() for line in downstream.text.split("\n"))

up_soup = BeautifulSoup(upstream_html, "html.parser")
down_soup = BeautifulSoup(downstream_html, "html.parser")

# Remove all <input> tags from the downstream as we don't need them
[i.extract() for i in down_soup.findAll('input')]

trs = down_soup.findAll('tr')


def extract_channel_data(table_rows):
    table_rows.pop(0)  # Remove the DS-1 etc row  as it's useless
    stat_count = len(table_rows)
    channel_count = len(table_rows[0]) - 1
    channel_data = {}

    for c in range(1, channel_count + 1 ):
        channel_data[c] = {}
        for r in range(1, stat_count):
            stat_name = table_rows[r].findAll('td')[0].text
            stat_value = table_rows[r].findAll('td')[c].text
            channel_data[c][stat_name] = stat_value
    return channel_data

ds_channel_data = extract_channel_data(down_soup.findAll('tr'))
us_channel_data = extract_channel_data(up_soup.findAll('tr'))

current_timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
rowcontent = [
    current_timestamp,
    us_channel_data[1]['Power Level (dBmV)'],
    us_channel_data[2]['Power Level (dBmV)'],
    us_channel_data[3]['Power Level (dBmV)'],
    us_channel_data[4]['Power Level (dBmV)'],
    ds_channel_data[1]['Power Level (dBmV)'],
    ds_channel_data[2]['Power Level (dBmV)'],
    ds_channel_data[3]['Power Level (dBmV)'],
    ds_channel_data[4]['Power Level (dBmV)'],
    ds_channel_data[5]['Power Level (dBmV)'],
    ds_channel_data[6]['Power Level (dBmV)'],
    ds_channel_data[7]['Power Level (dBmV)'],
    ds_channel_data[8]['Power Level (dBmV)'],
    ds_channel_data[1]['RxMER (dB)'],
    ds_channel_data[2]['RxMER (dB)'],
    ds_channel_data[3]['RxMER (dB)'],
    ds_channel_data[4]['RxMER (dB)'],
    ds_channel_data[5]['RxMER (dB)'],
    ds_channel_data[6]['RxMER (dB)'],
    ds_channel_data[7]['RxMER (dB)'],
    ds_channel_data[8]['RxMER (dB)'],
    ds_channel_data[1]['Pre RS Errors'],
    ds_channel_data[2]['Pre RS Errors'],
    ds_channel_data[3]['Pre RS Errors'],
    ds_channel_data[4]['Pre RS Errors'],
    ds_channel_data[5]['Pre RS Errors'],
    ds_channel_data[6]['Pre RS Errors'],
    ds_channel_data[7]['Pre RS Errors'],
    ds_channel_data[8]['Pre RS Errors'],
    ds_channel_data[1]['Post RS Errors'],
    ds_channel_data[2]['Post RS Errors'],
    ds_channel_data[3]['Post RS Errors'],
    ds_channel_data[4]['Post RS Errors'],
    ds_channel_data[5]['Post RS Errors'],
    ds_channel_data[6]['Post RS Errors'],
    ds_channel_data[7]['Post RS Errors'],
    ds_channel_data[8]['Post RS Errors']
]


def output_row_stdout(data):
    csv_writer = csv.writer(sys.stdout)
    csv_writer.writerow(data)


def output_row_csv(data):
    with open(options.outputfile, 'a') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(data)


def extract_channel_stat(channel, stat, data):
    for d in data:
        if data[d]["Channel ID"] == channel:
            return data[d][stat]

# If we aren't extracting a specific channel / stat then dump all the data to a csv row
if options.stat is None:
    # Either output the row to the specified file, or stdout if the -s flag was used
    if options.outputstdout:
        output_row_stdout(rowcontent)
    else:
        output_row_csv(rowcontent)
# Otherwise, extract the specific stat that we need
else:
    if options.statgroup == "ds":
        print(extract_channel_stat(options.channel, options.stat, ds_channel_data))
    elif options.statgroup == "us":
        print(extract_channel_stat(options.channel, options.stat, us_channel_data))

# All done. Bye-bye!
exit()
