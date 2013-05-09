#!/usr/bin/env python

import bitbucket
import os
import argparse
from getpass import getpass
import sys
import datetime
from urllib2 import HTTPError, URLError

_verbose=False
_quiet=False


def debug(message, output_no_verbose=False):
    """
    Outputs a message to stdout taking into account the options verbose/quiet.
    """
    global _quiet, _verbose
    if not _quiet and (output_no_verbose or _verbose):
        print "%s - %s" % (datetime.datetime.now(), message)


def exit(message, code=1):
    """
    Forces script termination using C based error codes.
    By default, it uses error 1 (EPERM - Operation not permitted)
    """
    global _quiet
    if not _quiet and message and len(message) > 0:
        sys.stderr.write("%s (%s)\n" % (message, code))
    sys.exit(code)


def exec_cmd(command):
    """
    Executes an external command taking into account errors and logging.
    """
    global _verbose
    debug("Executing command: %s" % command)
    if not _verbose:
        command = "%s > /dev/null 2>&1" % command
    resp = os.system(command)
    if resp != 0:
        exit("Command [%s] failed" % command, resp)


def compress(repo, location):
    """
    Creates a TAR.GZ file with all contents cloned by this script.
    """
    os.chdir(location)
    debug("Compressing repositories in [%s]..." % (location), True)
    exec_cmd("tar -zcvf bitbucket-backup-%s-%s.tar.gz `ls -d *`" % (repo.get('owner'), datetime.datetime.now().strftime('%Y%m%d%H%m%s')))
    debug("Cleaning up...", True)
    for d in os.listdir(location):
        path = os.path.join(location, d)
        if os.path.isdir(path):
            exec_cmd("rm -rfv %s" % path)


def clone_repo(repo, backup_dir, http, password):
    global _quiet, _verbose
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
            command = "git clone git@bitbucket.org:%s/%s.git %s" % (username, slug, backup_dir)
    if not command:
        exit("could not build command (scm [%s] not recognized?)" % scm)
    debug("Cloning %s..." % repo.get('name'))
    exec_cmd(command)


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
    if not command:
        exit("could not build command (scm [%s] not recognized?)" % scm)
    debug("Updating %s..." % repo.get('name'))
    exec_cmd(command)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Usage: %prog [options] ")
    parser.add_argument("-u", "--username", dest="username", help="Bitbucket username")
    parser.add_argument("-p", "--password", dest="password", help="Bitbucket password")
    parser.add_argument("-t", "--team", dest="team", help="Bitbucket team")
    parser.add_argument("-l", "--location", dest="location", help="Local backup location")
    parser.add_argument("-v", "--verbose", action='store_true', dest="verbose", help="Verbose output of all cloning commands")
    parser.add_argument("-q", "--quiet", action='store_true', dest="quiet", help="No output to stdout")
    parser.add_argument("-c", "--compress", action='store_true', dest="compress", help="Creates a compressed file with all cloned repositories (cleans up location directory)")
    parser.add_argument('--http', action='store_true', help="Fetch via https instead of SSH")
    parser.add_argument('--skip-password', dest="skip_password", action='store_true', help="Ignores password prompting if no password is provided (for public repositories)")
    args = parser.parse_args()
    username = args.username
    password = args.password
    owner = args.team if args.team else username
    location = args.location
    _quiet = args.quiet
    _verbose = args.verbose
    if _quiet:
        _verbose = False # override in case both are selected
    http = args.http
    if not password:
        if not args.skip_password:
            password = getpass(prompt='Enter your bitbucket password: ')
    if not username or not location:
        parser.error('Please supply a username and backup location (-u <username> -l <backup location>)')

    # ok to proceed
    try:
        bb = bitbucket.BitBucket(username, password, _verbose)
        user = bb.user(owner)
        repos = user.repositories()
        if not repos:
            print "No repositories found. Are you sure you provided the correct password"
        for repo in repos:
            debug("Backing up [%s]..." % repo.get("name"), True)
            backup_dir = os.path.join(location, repo.get("slug"))
            if not os.path.isdir(backup_dir):
                clone_repo(repo, backup_dir, http, password)
            else:
                debug("Repository [%s] already in place, just updating..." % repo.get("name"))
                update_repo(repo, backup_dir)
        if args.compress:
            compress(repo, location)
        debug("Finished!", True)
    except HTTPError, err:
        if err.code == 401:
            exit("Unauthorized! Check your credentials and try again.", 22) # EINVAL - Invalid argument
        else:
            exit("Connection Error! Bitbucket returned HTTP error [%s]." % err.code)
    except URLError, e:
        exit("Unable to reach Bitbucket: %s." % e.reason, 101) # ENETUNREACH - Network is unreachable
    except (KeyboardInterrupt, SystemExit):
        exit("Operation cancelled. There might be inconsistent data in location directory.", 0)
    except:
        if not _quiet:
            import traceback
            traceback.print_exc()
        exit("Unknown error.", 11) # EAGAIN - Try again
