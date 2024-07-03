# debian-lts-changelog-tool

Create a changelog file for the LTS of the specified distribution.
The data is created based on the email posted in the [LTS ML](https://lists.debian.org/debian-lts-changes/).

Last update: 2024-06-30

# How to use

## Get changelog data and create DB

The database is updated regularly and is committed to this repository. The
database is debian-lts-chanagelog.db. ML data is also stored in chagelog-data/.
To get data from January 2024 if you want, execute it as follows:

```
$ ./update-changelog-data.py -u -y 2024 -m 1
```

## Create changelog file

To create changelog file from '2024-01-01 00:00:00' to '2024-01-31 23:59:59',
execute it as follows:

```
$ ./create-changelog.py -d buster -f "2024-01-01 00:00:00" -t "2024-01-31 23:59:59"
# cat /tmp/chgangelog.txt
bind9 (1:9.11.5.P4+dfsg-5.1+deb10u10) buster-security; urgency=high
 .
   * Non-maintainer upload by the LTS Team.
   * CVE-2023-3341
     A stack exhaustion flaw was discovered in the control channel code
     which may result in denial of service (named daemon crash).
debian-security-support (1:10+2024.01.31) buster-security; urgency=medium
 .
   [ Santiago Ruano Rincón ]
   * Mark salt as non-supported in buster. (MR: debian/debian-security-support!22)
 .
   [ Holger Levsen ]
   * Add tiles to security-support-limited, Closes: #1057343.
   * Drop debian/.gitlab-ci.yml.
exim4 (4.92-8+deb10u9) buster-security; urgency=high
[...]
```

# License

Apache 2.0
