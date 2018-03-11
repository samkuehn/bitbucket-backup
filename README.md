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
bitbucket-backup [-u <bitbucket_username>] [-p <bitbucket_password>] [-k <oauth_key>] [-s <oauth_secret>]
  [-l <local_backup_location>] [-t <bitbucket_team>] [-a] [-v] [-q] [-c] [--http] [--skip-password] [--mirror]
  [--prune] [--fetchlfs]
```
Username/password, or OAuth credentials, are needed to access the bitbucket api to get a repo listing.
At this time it is not used to do the clone/update.
Clone/update requires that your ssh keys have been uploaded to bitbucket.

You can backup a team's repositories instead of your own by supplying the optional `-t` parameter.

## OAuth authentication
You can use OAuth authentication if you do not want to use username/password. There are 4 steps to using OAuth.

1. Create OAuth consumer keys here: `https://bitbucket.org/account/user/<username>/api`
2. Make sure that your consumer has the following permissions:
    - Account: Read
    - Projects: Read
    - Repositories: Read
3. Specify the `-k <oauth_key> -s <oauth_secret>` flags
4. Make sure oauthlib is installed `pip install oauthlib`

## Requirements

You do need to have your ssh keys uploaded for the computer that you are running the backup on.
If you would like to use OAuth authentication you need to install oauthlib `pip install oauthlib`.

## Additional notes
I am hosting this on GitHub because I believe it is superior for public repos (I understand the irony).
