#!/usr/bin/env python3

"""
SPDX-License-Identifier: Apache-2.0
Copyright 2024 Nobuhiro Iwamatsu <iwamatsu@nigauri.org>
"""

import re
import os
import sys
import gzip
import shutil
import subprocess
import argparse
# apt install python3-apt
import apt_pkg
import requests
import yaml

FREEXIAN_MIRROR = "https://deb.freexian.com/extended-lts/"
DEBIAN_MIRROR = 'http://deb.debian.org/debian/'
DEBIAN_LTS_MIRROR = 'https://security.debian.org/debian-security/'

class DebianLTSChangelogs:
    
    suite = None
    maint_mode = None
    apt_pkg.init_system()

    section = {}
    esr = ['firefox-esr']

    def __init__(self, suite: str, maint_mode:str = None):

        if suite is None:
            print ('Please set suite.')
            return

        self.suite = suite
        if maint_mode is None:
            if self.suite == 'buster':
                self.maint_mode = 'elts'
            elif self.suite == 'bullseye':
                self.maint_mode = 'lts'
        else:
            self.maint_mode = maint_mode

        self.section['buster'] = ['main', 'contrib', 'non-free']
        self.section['bullseye'] = ['main', 'contrib', 'non-free']
        self.section['bookworm'] = ['main', 'contrib', 'non-free', 'non-free-firmware']
        self.section['stable'] = ['main', 'contrib', 'non-free', 'non-free-firmware']

    """
    def __del__(self):
    """

    def get_section_list(self):
            return self.section[self.suite]

    def save_debian_source_packages(self, directory_path, package_filename):

        save_filename = f'temp/{package_filename}'

        try:
            os.makedirs('temp')
        except:
            pass

        try:
            url_data = None

            if self.maint_mode == 'elts':
                url = f'{FREEXIAN_MIRROR}/{directory_path}/{package_filename}'
            elif self.maint_mode == 'lts':
                url = f'{DEBIAN_LTS_MIRROR}/{directory_path}/{package_filename}'
            else:
                url = f'{DEBIAN_MIRROR}/{directory_path}/{package_filename}'

            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print("    Info: ", e)
            return
        else:
            package_data = response.content

        if package_data is None:
            print (f'    No data for {package_filename} source package')
            return

        print (f'    Save filename: {save_filename} ')
        with open(save_filename, mode='wb') as f:
            f.write(package_data)

    """
    def generate_changelog(self, package_name, package_data, lts_latest_version):

        directory = package_data['directory']
        package_version = package_data['version']
        dirname = os.path.join('changelogs', self.suite, directory.replace('pool/', ''))
        generate_changelog_filename = f'/tmp/changelog.{self.suite}'

        changelog_filename = os.path.join(dirname, package_name) + '.changelog'
        if not os.path.exists(changelog_filename):
            print ('    No changelog file')
            return False

        changelog_data_f = False
        with open(generate_changelog_filename, mode='w') as fout:
            with open(changelog_filename, mode='r') as fin:
                for line in fin:
                    if package_version in line:
                        changelog_data_f = True
                    elif lts_latest_version in line:
                        break

                    if changelog_data_f == True:
                        print ('write')
                        fout.write(line)
    """

    def generate_changelog(self, package_name, directory, elts_version, lts_latest_version):

        directory = directory.replace('pool/', '').replace('updates/', '')
        dirname = os.path.join('changelogs', self.suite, directory)
        generate_changelog_filename = f'/tmp/changelog.{self.suite}'

        changelog_filename = os.path.join(dirname, package_name) + '.changelog'
        if not os.path.exists(changelog_filename):
            print ('    No changelog file')
            return False

        changelog_data_f = False
        write_mode = 'w'
        if os.path.isfile(generate_changelog_filename):
            write_mode = 'a'

        with open(generate_changelog_filename, mode = write_mode) as fout:
            with open(changelog_filename, mode='r') as fin:
                for line in fin:
                    __package_name = package_name
                    # for mozilla's software
                    if __package_name in self.esr:
                        __package_name = __package_name.replace('-esr','')
                    if re.search(f'^{__package_name}', line):
                        reg = '(?<=\\().+?(?=\\))'
                        version_line = re.findall(reg, line)[0]

                        if version_line == elts_version:
                            changelog_data_f = True
                        if version_line == lts_latest_version:
                            break
                        if self.version_compare(lts_latest_version, version_line) > 0:
                            break

                    if changelog_data_f == True:
                        fout.write(line)

    def generate_changelogs(self, packages_list):

        for package_name in packages_list:
            directory = packages_list[package_name]['directory']
            target_version = packages_list[package_name]['target_version']
            base_version = packages_list[package_name]['base_version']

            self.generate_changelog(package_name, directory, target_version, base_version)

    def get_package_version(self, package_name, package_data):

        directory = package_data['directory'].replace('pool/', '').replace('updates/', '')
        dirname = os.path.join('changelogs', self.suite, directory)
        versionfile = os.path.join(dirname, 'VERSION')

        # Note: read from changelogs of head?
        if os.path.isfile(versionfile):
            with open(versionfile, mode='r') as f:
                for line in f:
                    return line.rstrip('\n')
        else:
            return None

    def version_compare(self, target_version, base_version):

        return apt_pkg.version_compare(target_version, base_version)

    def save_and_update_changelog(self, package_name, package_data):

        directory = package_data['directory']
        package_version = package_data['version']
        dirname = os.path.join('changelogs', self.suite, directory.replace('pool/', ''))
        # for LTS
        dirname = dirname.replace('updates/', '')
        versionfile = os.path.join(dirname, 'VERSION')

        print (f'{package_name}:')

        try:
            os.makedirs(dirname)
        except:
            pass

        if os.path.isfile(versionfile):
            with open(versionfile, mode='r') as f:
                for line in f:
                    line = line.rstrip('\n')
                    if line == package_version:
                        print ('    There are already updated files.')
                        # No update
                        return package_version

        if 'tar.gz' in package_data:
            debian_file_format = 'tar.gz'
        if 'orig.tar' in package_data:
            debian_file_format = 'orig.tar'
        elif 'diff.gz' in package_data:
            debian_file_format = 'diff.gz'
        elif 'debian.tar' in package_data:
            debian_file_format = 'debian.tar'
        else:
            print ('    No download file')
            return None

        download_filename = package_data[debian_file_format]
        self.save_debian_source_packages(directory, download_filename)

        # extract
        try:
            if debian_file_format == 'diff.gz':
                with gzip.open('temp/' + download_filename, 'rb') as fin:
                    with open('temp/diff.patch', 'wb') as fout:
                        shutil.copyfileobj(fin, fout)
            else:
                shutil.unpack_archive('temp/' + download_filename, 'temp/')
        except:
            print (f'    Can not open temp/{download_filename}')
            return None

        if debian_file_format == 'diff.gz':
            try:
                os.system('patch -f -p1 -d temp < temp/diff.patch > /dev/null')
                """
                proc = subprocess.Popen('patch -f -p1 -d temp < temp/diff.patch'.split(' '),
                            cwd = "/home/iwamatsu/dev/debian/debian-repo-checker",
                            shell = True,
                            stdin  = subprocess.PIPE,
                            stdout = subprocess.PIPE,
                            stderr = subprocess.PIPE)
                stdout_data, stderr_data = proc.communicate()
			"""
            except:
                print("    os.system() failed")
                return None

        changelog_filename = os.path.join(dirname, package_name) + '.changelog'

        debian_dir_list = [
            f for f in os.listdir('temp') if os.path.isdir(os.path.join('temp', f))
        ]

        if 'debian' in debian_dir_list:
            debian_package_changelog = os.path.join('temp', 'debian/changelog')
        else:
            debian_package_changelog = os.path.join('temp', debian_dir_list[0], 'debian/changelog')

        if os.path.exists(debian_package_changelog):
            shutil.copy(debian_package_changelog, changelog_filename)
        else:
            print ('    No changelog file')
            shutil.rmtree('temp')
            return None

        with open(versionfile, mode='w') as f:
            f.write(package_version)

        shutil.rmtree('temp')

        return package_version
 
    def parse_meta_data(self, section:str = 'main', base_parse_data = None):

        section_list = self.get_section_list()
        if section not in section_list:
            print ('    Section {section} is not support with {self.suite}')
            return

        filename = f'Sources-{self.suite}-{self.maint_mode}-{section}'

        if base_parse_data:
            parse_data = base_parse_data
        else:
            parse_data = {}

        with open(filename) as f:
            package_name = ""
            package_version = ""
            package_filename = ""
            package_directory = ""
            package_info = {}
            update_info = False

            line = f.readline()
            while line:
                line = line.rstrip('\n')
                if re.search('^Package: ', line) != None:
                    package_name = line.replace('Package: ', '')

                    if package_name in parse_data:
                        package_info = parse_data[package_name]
                elif re.search('^Version: ', line) != None:
                    package_version = line.replace('Version: ', '')

                    if 'version' in package_info:
                        current_version = package_info['version']
                        version_compare = apt_pkg.version_compare(package_version, current_version)
                        if version_compare > 0:
                            package_info['version'] = package_version
                            update_info = True
                    else:
                        package_info['version'] = package_version

                elif re.search('^Format:', line) != None:
                    package_format = line.rstrip('\n').replace('Format: ', '')
                    package_info['format'] = package_format

                elif re.search('^Checksums-Sha256:', line) != None:
                    # read next line
                    line = f.readline()
                    if package_info['format'] == '1.0':
                        while line:
                            if '.tar.gz' in line and '.orig.tar.gz' not in line:
                                src_package_elements = line.rstrip('\n').lstrip('  ').split(' ')
                                package_info['tar.gz'] = src_package_elements[2]
                                break
                            elif '.diff.gz' in line:
                                src_package_elements = line.rstrip('\n').lstrip('  ').split(' ')
                                package_info['diff.gz'] = src_package_elements[2]
                                break
                            else:
                                line = f.readline()
                                continue

                    elif package_info['format'] == '3.0 (native)':
                            # Read next line
                            line = f.readline()
                            src_package_elements = line.rstrip('\n').lstrip('  ').split(' ')
                            package_info['orig.tar'] = src_package_elements[2]

                    elif package_info['format'] == '3.0 (quilt)':
                        while line:
                            if '.debian.tar.' in line:
                                src_package_elements = line.rstrip('\n').lstrip('  ').split(' ')
                                package_info['debian.tar'] = src_package_elements[2]
                                break
                            else:
                                line = f.readline()
                                continue
                    else:
                        print (f'    {package_name} does not have package format data.')
                        return

                elif re.search('^Directory: ', line) != None:
                    package_directory = line.replace('Directory: ', '')
                    if 'directory' in package_info:
                        if update_info == True:
                            package_info['directory'] = package_directory
                    else:
                        package_info['directory'] = package_directory

                elif len(line) == 0:
                    parse_data[package_name] = package_info
                    package_name = ""
                    package_version = ""
                    package_filename = ""
                    package_directory = ""
                    package_info = {}

                line = f.readline()

            # for last data
            if len(package_name) != 0:
                parse_data[package_name] = package_info

        return parse_data

    def __download_sources_file(self, source_url:str, save_filename:str):

        # TODO error check
        url_data = requests.get(source_url).content

        # TODO error check
        with open('Sources.gz', mode='wb') as f:
            f.write(url_data)

        # TODO error check
        with gzip.open("Sources.gz", mode="rb") as gzip_file:
            with open(save_filename, mode="wb") as decompressed_file:
                shutil.copyfileobj(gzip_file, decompressed_file)

        return True

    def download_sources_files(self, source_url:str = None):

        if source_url is not None:
            save_filename = f'Sources-{self.suite}-{self.maint_mode}-main'
            return self.__download_sources_file(source_url, save_filename)

        section_list = self.section[self.suite]

        for section in section_list:
            if self.maint_mode == "elts":
                if self.suite == "buster":
                    url = f'http://deb.freexian.com/extended-lts/dists/{self.suite}-lts/{section}/source/Sources.gz'
                else:
                    print (f'    {self.suite} does not support.')
                    return False
            if self.maint_mode == "lts":
                if self.suite == "buster":
                    url = f'https://security.debian.org/debian-security/dists/{self.suite}/updates/{section}/source/Sources.gz'
                elif self.suite == "bullseye":
                    url = f'https://security.debian.org/debian-security/dists/{self.suite}-security/{section}/source/Sources.gz'
                else:
                    print (f'    {self.suite} does not support.')
                    return False
            elif self.maint_mode == "stable":
                url = f'http://deb.debian.org/debian/dists/{self.suite}/{section}/source/Sources.gz'

            save_filename = f'Sources-{self.suite}-{self.maint_mode}-{section}'
            ret = self.__download_sources_file(url, save_filename)
            if ret != True:
                return False

        return True

