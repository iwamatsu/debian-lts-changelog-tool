# Debian ELTS changelog tools

# How to use

1. Get the latest ELTS package information and package changelog.

When run, it will download the Sources.gz for the ELTS. Next,
it downloads the changelog files for the packages managed in the
repository into the changelogs directory.

For Debian 10 (buster):
```
./update-debian-elts-changelogs.py -s buster
```

2. Create changelog diff between Debian stable + Debian LTS to /tmp/changelog.SUITE.

Download Sources.gz for Debian stable and Debian LTS.
Output d/changelog of updated packages to /tmp/changelog.SUITE.  

```
$ ./generate-debian-elts-changelogs.py -s buster
$ head /tmp/changelog.buster
aom (1.0.0-3+deb10u2) buster-security; urgency=medium

  * Non-maintainer upload by the ELTS Team.
  * CVE-2024-5171: Integer overflows

 -- Adrian Bunk <bunk@debian.org>  Wed, 31 Jul 2024 22:12:43 +0300

apache2 (2.4.59-1~deb10u4) buster-security; urgency=medium

  * Team upload by ELTS team
```

If you want to target Sources.gz other than Debian stable and Debian LTS,
use the --url option.
 
For Debian 10 (buster):
```
$ ./generate-debian-elts-changelogs.py -s buster \
    -u http://deb.freexian.com/extended-lts/dists/buster-lts/main/source/Sources.gz
$ head /tmp/changelog.buster
[Maybe, no outout]
```

# License

    Apache 2.0


