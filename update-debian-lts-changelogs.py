#!/usr/bin/env python3

"""
SPDX-License-Identifier: Apache-2.0
Copyright 2024 Nobuhiro Iwamatsu <iwamatsu@nigauri.org>
"""

import sys
import argparse
from debian_lts_changelogs import DebianLTSChangelogs

def main():
    parser = argparse.ArgumentParser(description='Debian chagelog')
    parser.add_argument('-s', '--suite', \
        type = str, help='target suite', required=True)
    
    args = parser.parse_args()

    lts = DebianLTSChangelogs(args.suite)

    if not lts.download_sources_files():
        print ('Could not download sources file.')
        sys.exit()

    section_list = lts.get_section_list()
    
    for section in section_list:
        target_data = lts.parse_meta_data(section)

        for package_name in target_data:
            lts.save_and_update_changelog(package_name, target_data[package_name])

if __name__ == "__main__":
    main()
