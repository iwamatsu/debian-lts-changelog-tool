#!/usr/bin/env python3

"""
Get the package Changelog from the email in debian-lts-changes ML
and save it to the chagelog-data directory.
"""

import sys
import argparse
from debian_lts_packages import DebianLTSPackages

def main():
    parser = argparse.ArgumentParser(description='Debian lts changelog updater')
    parser.add_argument('-m', '--month', type = int, help='month')
    parser.add_argument('-y', '--year', type = int, help='year')
    parser.add_argument('-d', '--distribution', type = str, help='distribution')
    parser.add_argument('-u', '--updatedb', help='update db', action='store_true')

    args = parser.parse_args()

    if args.year == None:
        print ("no year arg")
        sys.exit(1)

    lts = DebianLTSPackages(args.updatedb)

    if args.month == None:
        lts.get_year_data(args.year)
    else:
        lts.get_month_data(args.year, args.month)

if __name__ == "__main__":
    main()
