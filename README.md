#Bitbucket backup

[![Build Status](https://travis-ci.org/samkuehn/bitbucket-backup.svg?branch=master)](https://travis-ci.org/samkuehn/bitbucket-backup)

## Description
This python script will backup all of your bitbucket repos (both mercurial and git) locally.
If the repository does not exist locally the repo will be cloned to the <local_backup_location>.
If the repo does exist locally an `hg pull` will be run for mercurial repos,
an `git remote update` will be run for git repos.

## Installation

```bash
pip install https://github.com/samkuehn/bitbucket-backup/archive/master.zip
```

## Quickstart
```bash
bitbuckt-backup [-u <bitbucket_username>] [-l <local_backup_location>]
  [-p <bitbucket_password>] [-t <bitbucket_team>] [-v] [-q] [-c] [--http] [--skip-password] [--mirror]
```
The password is needed to access the bitbucket api's.  At this time it is not used to do the clone/update.
Clone/update requires that your ssh keys have been uploaded to bitbucket.

You can backup a team's repositories instead of your own by supplying the optional `-t` parameter.

## Requirements

You do need to have your ssh keys uploaded for the computer that you are running the backup on.

## Additional notes
I am hosting this on GitHub because I believe it is superior for public repos (I understand the irony).
