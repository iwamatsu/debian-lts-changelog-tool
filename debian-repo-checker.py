#!/usr/bin/env python3

"""
SPDX-License-Identifier: Apache-2.0
Copyright 2024 Nobuhiro Iwmaatsu <iwamatsu@nigauri.org>
"""

import re
import argparse
# apt install python3-apt
import apt_pkg

def parse_meta_data(filename, apt):
    parse_data = {}
    with open(filename) as f:
        package_name = ""
        package_version = ""
        for line in f:
            line = line.rstrip('\n')
            if re.search('^Package: ', line) != None:
                package_name = line.replace('Package: ', '')
            elif re.search('^Version: ', line) != None:
                package_version = line.replace('Version: ', '')
                if package_name in parse_data:
                    current_version = parse_data[package_name]
                    version_compare = apt.version_compare(package_version, current_version)
                    if version_compare > 0:
                        parse_data[package_name] = package_version
                else:
                    parse_data[package_name] = package_version

                package_name = ""
                package_version = ""
    return parse_data

def main():
    parser = argparse.ArgumentParser(description='Debian repository checker')
    parser.add_argument('-t', '--target', \
            type = str, help='target file', required=True)
    parser.add_argument('-b', '--based', \
            type = str, help='based files', required=True)

    args = parser.parse_args()
    apt_pkg.init_system()

    target_data = parse_meta_data(args.target, apt_pkg)

    based_file_data = {}
    based_files = args.based

    for based_file in based_files.split(","):
        if len(based_file_data) == 0:
            based_file_data = parse_meta_data(based_file, apt_pkg)
        else:
            based_file_data = based_file_data | parse_meta_data(based_file, apt_pkg)

    for package_name in based_file_data:
        if package_name in target_data:
            target_version = target_data[package_name]
            based_version = based_file_data[package_name]
        else:
            print (f"@@@@@ {package_name} not in target @@@@@")
            continue

        version_compare = apt_pkg.version_compare(target_version, based_version)
        if version_compare < 0:
            print(f'##### {package_name}: version target({target_version}) < version base({based_version})')
        """
        elif version_compare == 0:
            print(f'{package_name}: version target({target_version}) == version base({based_version})')
        elif version_compare > 0:
            print(f'{package_name}: version target({target_version}) > version base({based_version})')
        """

if __name__ == "__main__":
    main()
