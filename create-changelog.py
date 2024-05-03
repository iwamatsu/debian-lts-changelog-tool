#!/usr/bin/env python3

"""
Create changelog data from database.
"""

import argparse
from debian_lts_packages import DebianLTSPackages

def main():
    parser = argparse.ArgumentParser(description='Debian lts changelog careater')
    parser.add_argument('-d', '--distribution', \
            type = str, help='distribution', required=True, choices=['stretch', 'buster'])
    parser.add_argument('-f', '--datefrom', \
            type = str, help='date from: YY-MM-DD HH:MM:SS', required=True)
    parser.add_argument('-t', '--dateto', \
            type = str, help='date to: YY-MM-DD HH:MM:SS', required=True)
    parser.add_argument('-o', '--output', \
            type = str, help='output file', default = '/tmp/changelog.txt')

    args = parser.parse_args()
    lts = DebianLTSPackages(True)

    # TODO: Add format check
    lts.create_changelog(args.distribution, args.datefrom, args.dateto, args.output)

if __name__ == "__main__":
    main()
