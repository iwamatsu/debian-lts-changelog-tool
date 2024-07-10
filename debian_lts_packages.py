#!/usr/bin/env python3

"""
Get the package Changelog from the email in debian-lts-changes ML
and save it to the chagelog-data directory.
"""

import sys
import os
import re
import sqlite3
from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.error import HTTPError
from datetime import datetime                                                   
from email.utils import parsedate_tz, mktime_tz

base_url = "https://lists.debian.org/debian-lts-changes"
dbname = "debian-lts-chanagelog.db"

class DebianLTSPackages:
    sql_conn = None
    updatedb = True

    def __init__(self, updatedb: bool):
        self.updatedb = updatedb
        if self.updatedb:
            self.sql_conn = sqlite3.connect(dbname)
            self.__create_table()
        pass

    def __del__(self):
        if self.sql_conn != None:
            self.sql_conn.close()

    def __create_table(self):
        if self.updatedb == False:
            return
        if self.sql_conn == None:
            return

        cur = self.sql_conn.cursor()
        sql_cmd = f"""CREATE TABLE IF NOT EXISTS package_data(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    update_date TEXT NOT NULL, 
                    update_time TEXT NOT NULL, 
                    upload_date TEXT NOT NULL, 
                    upload_time TEXT NOT NULL, 
                    distribution TEXT NOT NULL, 
                    upload_info TEXT NOT NULL, 
                    file_path TEXT NOT NULL
        )"""

        cur.execute(sql_cmd)
        cur.close()
        self.sql_conn.commit()

    def get_changelog_data_all(self, mail_text_data: str) -> str:
        target = "-----BEGIN PGP SIGNED MESSAGE-----\n"
        idx_s = mail_text_data.find(target)
        idx_e = mail_text_data.find("-----BEGIN PGP SIGNATURE-----\n")

        # Extract Changelog
        changelog_data = mail_text_data[idx_s + len(target):idx_e]

        changelog_data_list = changelog_data.split('\n')
        # Remove head of white space from first line
        changelog_data_list[0] = changelog_data_list[0].lstrip()
        # change form list to string
        changelog_data = "\n".join(changelog_data_list)

        return changelog_data

    # Changelog only
    def get_changelog_data_main(self, text_data: str) -> str:
        target = "Changes:\n"
        idx_s = text_data.find(target)
        idx_e = text_data.find("Checksums-Sha1:")
        if idx_s > idx_e:
            idx_e = text_data.find("Files:")
        if idx_s > idx_e:
            idx_e = text_data.find("Checksums-Sha256:")

        # Extract Changelog
        changelog_data = text_data[idx_s + len(target):idx_e]

        changelog_data_list = changelog_data.split('\n')
        # Remove head of white space from first line
        changelog_data_list[0] = changelog_data_list[0].lstrip()
        # change form list to string
        changelog_data = "\n".join(changelog_data_list)

        return changelog_data

    def get_package_info(self, changelog_data: str):
        changelog_data_str = self.get_changelog_data_main(changelog_data)

        changelog_data_list = changelog_data_str.split('\n')
        package_data_list = changelog_data_list[0].split(' ')

        src_package_name = package_data_list[0]
        src_package_ver = package_data_list[1].strip('(').strip(')')
        dist = package_data_list[2].strip(';')

        return (src_package_name, src_package_ver, dist)

    def convert_rfc2822_to_sqlitedate_utc(self, date_data: str) -> str:
        time_data_tuple = parsedate_tz(date_data)                                               
        time_data_stamp = mktime_tz(time_data_tuple)
        
        return str(datetime.utcfromtimestamp(time_data_stamp))

    def get_pkg_update_date(self ,changelog_data: str) -> str:
        pattern = re.compile("^Date: (.*)$", re.MULTILINE) 
        matched_data = pattern.findall(changelog_data)
        if matched_data is None:
            print ("No matched data")
            return None
        return matched_data[0]

    def get_pkg_upload_date(self, bs4)-> str:
        list_data = bs4.find_all("li")
        for li in list_data:
            if li.em == None:
                continue
            if li.em.string != "Date":
                continue
            else:
                return li.get_text().strip("Date: ")
        return None

    def get_data(self, year: int, month: int, count: int) -> bool:
        url = "%s/%d/%02d/msg%05d.html" % (base_url, year, month, count)

        try:
            html = urlopen(url)
            data = html.read()
            html = data.decode('utf-8')

        except HTTPError as e:
            print(f"Can not read data: {url}: {e.code} - {e.reason}")
            if count != 0:
                print(f"\tMaybe latest data.")

            return False

        soup = BeautifulSoup(html, 'html.parser')

        upload_date = self.get_pkg_upload_date(soup)
        if upload_date == None:
            print ("No upload date")
            return False
        upload_date = self.convert_rfc2822_to_sqlitedate_utc(upload_date)

        pre_data = soup.find_all("pre")
        for pre in pre_data:
            if "BEGIN PGP SIGNED MESSAGE" in pre.get_text():
                changelog_text_data = self.get_changelog_data_all(pre.get_text())
                self.save_changelog_data(year, month, count, changelog_text_data, upload_date)
                return True
        return False

    def save_changelog_data(self, year, month, count, text_data, pkg_upload_date_all):
        pkg_data = self.get_package_info(text_data)
        if pkg_data == None:
            print(f"No data : %d/%02d/msg%05d.html" % (year, month, count))
            return

        # update date
        pkg_update_date_all = self.get_pkg_update_date(text_data)
        if pkg_update_date_all == None:
            print(f"Could not get date for update: %d/%02d/msg%05d.html" % (year, month, count))
            return
        pkg_update_date_all = self.convert_rfc2822_to_sqlitedate_utc(pkg_update_date_all)
        __pkg_update_date_all = pkg_update_date_all.split(' ')
        pkg_update_date = __pkg_update_date_all[0]
        pkg_update_time = __pkg_update_date_all[1]
        # upload date
        __pkg_upload_date_all = pkg_upload_date_all.split(' ')
        pkg_upload_date = __pkg_upload_date_all[0]
        pkg_upload_time = __pkg_upload_date_all[1]

        dir_path = "chagelog-data/%d/%02d" % (year, month)
        file_path = "%s/msg%05d" % (dir_path, count)
        pkg_name = pkg_data[0]
        pkg_version = pkg_data[1]
        distribution = pkg_data[2]

        symlink_path = "%s/%s@%s" % (dir_path, pkg_name, pkg_version)
        
        if os.path.isdir(dir_path):
            pass
        else:
            os.makedirs(dir_path)

        with open(file_path, mode='w') as f:
            f.write(text_data)

        is_file = os.path.isfile(symlink_path)
        if is_file == False:
            os.symlink("msg%05d" % (count), symlink_path)

        if self.updatedb == False:
            return

        cur = self.sql_conn.cursor()
        # ' -> ''
        text_data = text_data.replace("'", "''")

        sql_cmd = f"""INSERT INTO
                    package_data (name, version, update_date, update_time, upload_date, upload_time, distribution, upload_info, file_path) 
                    SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?
                    WHERE NOT EXISTS (SELECT * FROM package_data WHERE name = ? AND version = ?) ;
                    """   
        try:
            cur.execute(sql_cmd,
                        (pkg_name, pkg_version, pkg_update_date, pkg_update_time,
                         pkg_upload_date, pkg_upload_time, distribution, text_data,
                         file_path, pkg_name, pkg_version))

        except Exception as e:
            print('Exception: {}'.format(e))

        cur.close()
        self.sql_conn.commit()
    
    def get_month_data(self, year: int, month: int):
        count = 0
        while True:
            if self.get_data(year, month, count) == False:
                break
            count += 1

    def get_year_data(self, year: int):
        for month in range (1, 13):
            get_month_data(year, month)

    def create_changelog(self, distribution: str, date_from: str, date_to: str, output_file: str) -> None:
        if os.path.isfile(output_file):
            os.remove(output_file)

        cur = self.sql_conn.cursor()

        date_from_date = date_from.split(' ')[0]
        date_from_time = date_from.split(' ')[1]
        date_to_date = date_to.split(' ')[0]
        date_to_time = date_to.split(' ')[1]

        distribution_sec = f'{distribution}-security'
        sql = f"""SELECT name, version, upload_date, upload_time, upload_info
                  FROM package_data WHERE datetime(upload_date || " " || update_time) >= datetime(?) and datetime(upload_date || " " || update_time) <= datetime(?) and distribution IN (?, ?)
                  ORDER BY name ASC, upload_date DESC;"""
        cur.execute(sql, (date_from, date_to, distribution, distribution_sec))
        with open(output_file, mode='a') as f:
            for fetch_data in cur.fetchall():
                f.write(self.get_changelog_data_main(fetch_data[4]))

        cur.close()
