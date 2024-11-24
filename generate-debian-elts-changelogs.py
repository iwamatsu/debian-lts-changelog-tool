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
    parser.add_argument('-u', '--url', \
        type = str, help='target sources.gz url')
    
    args = parser.parse_args()

    elts = DebianLTSChangelogs(args.suite, maint_mode = 'elts')

    base_data = {}
    if args.url is None:
        stable = DebianLTSChangelogs(args.suite, maint_mode = 'stable')
        if not stable.download_sources_files():
            print ('Could not download sources file.')
            sys.exit()

        section_list = stable.get_section_list()

        for section in section_list:
            base_data = stable.parse_meta_data(section, base_data)

        lts = DebianLTSChangelogs(args.suite, maint_mode = 'lts')
        if not lts.download_sources_files():
            print ('Could not download sources file.')
            sys.exit()

        section_list = lts.get_section_list()
        for section in section_list:
            base_data = lts.parse_meta_data(section, base_data)
    else:
        base = DebianLTSChangelogs(args.suite, maint_mode = 'stable')
        if not base.download_sources_files(args.url):
            print ('Could not download sources file.')
            sys.exit()

        base_data = base.parse_meta_data()

    packages_list = {}
    for package_name in base_data:
        print(f'Check {package_name}:')
        base_version = base_data[package_name]['version']
        target_version = elts.get_package_version(package_name, base_data[package_name])

        if target_version is None:
            print('    No version data.')
            continue

        version_compare = elts.version_compare(target_version, base_version)
        if version_compare > 0:
            print(f'    Updated {package_name} from {base_version} to {target_version}')

            package_info = {}
            package_info['base_version'] = base_version;
            package_info['target_version'] = target_version;
            package_info['directory'] = base_data[package_name]['directory']

            packages_list[package_name] = package_info;
        """
        if version_compare < 0:
            print(f'    base {package_name} is old version (base: {based_version}, target: {target_version})')
        if version_compare == 0:
            print(f'    {package_name} is same version (base: {based_version}, target: {target_version})')
        """ 

    packages_list_sorted = dict(sorted(packages_list.items(), key=lambda x:x[0]))
    elts.generate_changelogs(packages_list_sorted)

if __name__ == "__main__":
    main()
