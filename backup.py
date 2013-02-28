#!/usr/bin/env python

import bitbucket
import os
import argparse
from getpass import getpass


def clone_repo(repo, backup_dir, http, password):
    scm = repo.get('scm')
    slug = repo.get('slug')
    username = repo.get('owner')
    command = None
    if scm == 'hg':
        if http:
            command = 'hg clone https://%s:%s@bitbucket.org/%s/%s %s' % (username, password, username, slug, backup_dir)
        else:
            command = 'hg clone ssh://hg@bitbucket.org/%s/%s %s' % (username, slug, backup_dir)
    if scm == 'git':
        if http:
            command = "git clone https://%s:%s@bitbucket.org/%s/%s.git %s" % (username, password, username, slug, backup_dir)
        else:
            #command = "git clone --mirror git@bitbucket.org:%s/%s.git %s" % (username, slug, backup_dir)
            command = "git clone git@bitbucket.org:%s/%s.git %s" % (username, slug, backup_dir)
    if not command:
        return
    print command
    os.system(command)


def update_repo(repo, backup_dir):
    scm = repo.get('scm')
    command = None
    os.chdir(backup_dir)
    if scm == 'hg':
        command = 'hg pull -u'
    if scm == 'git':
        command = 'git remote update'
    if not command:
        return
    print command
    os.system(command)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Usage: %prog [options] ")
    parser.add_argument("-u", "--username", dest="username", help="Bitbucket username")
    parser.add_argument("-p", "--password", dest="password", help="Bitbucket password")
    parser.add_argument("-l", "--location", dest="location", help="Local backup location")
    parser.add_argument('--http', action='store_true', help="Fetch via https")
    args = parser.parse_args()
    username = args.username
    password = args.password
    location = args.location
    http = args.http
    if not password:
        password = getpass(prompt='Enter your bitbucket password: ')
    if not username or not location:
        parser.error('Please supply a username and backup location (-u <username> -l <backup location>)')
    if not os.path.isdir(location):
        print "Backup location does not exist.  Please provide an existing directory."
    bb = bitbucket.BitBucket(username, password)
    user = bb.user(username)
    repos = user.repositories()
    if not repos:
        print "No repositories found.  Are you sure you provided the correct password"
    for repo in repos:
        print "Backing up %s" % repo.get("name")
        backup_dir = os.path.join(location, repo.get("slug"))
        if not os.path.isdir(backup_dir):
            clone_repo(repo, backup_dir, http, password)
        else:
            update_repo(repo, backup_dir)
