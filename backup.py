#!/usr/bin/env python
import argparse
import base64
import datetime
import os
import shutil
import subprocess
import sys
from getpass import getpass

try:
    from urllib.error import HTTPError, URLError
except ImportError:
    from urllib2 import HTTPError, URLError

try:
    from urllib.request import Request, urlopen
except ImportError:
    from urllib2 import Request, urlopen

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote

try:
    input = raw_input
except NameError:
    pass

try:
    import json
except ImportError:
    import simplejson as json

try:
    _range = xrange
except NameError:
    _range = range

_verbose = False
_quiet = False


class MaxBackupAttemptsReached(Exception):
    pass


def debug(message, output_no_verbose=False):
    """
    Outputs a message to stdout taking into account the options verbose/quiet.
    """
    global _quiet, _verbose
    if not _quiet and (output_no_verbose or _verbose):
        print("%s - %s" % (datetime.datetime.now(), message))


def exit(message, code=1):
    """
    Forces script termination using C based error codes.
    By default, it uses error 1 (EPERM - Operation not permitted)
    """
    global _quiet
    if not _quiet and message and len(message) > 0:
        sys.stderr.write("%s (%s)\n" % (message, code))
    sys.exit(code)


def exec_cmd(command, stop_on_error=True):
    """
    Executes an external command taking into account errors and logging.
    """
    global _verbose
    debug("Executing command: %s" % command)
    if not _verbose:
        if "nt" == os.name:
            command = "%s > nul 2> nul" % command
        else:
            command = "%s > /dev/null 2>&1" % command
    resp = subprocess.call(command, shell=True)
    if resp != 0:
        if stop_on_error:
            exit("Command [%s] failed" % command, resp)
        else:
            debug("Command [%s] failed: %s" % (command, resp))


def compress(repo, location):
    """
    Creates a TAR.GZ file with all contents cloned by this script.
    """
    os.chdir(location)
    debug("Compressing repositories in [%s]..." % location, True)
    exec_cmd(
        "tar -zcvf bitbucket-backup-%s-%s.tar.gz `ls -d *`"
        % (
            repo.get("owner").get("username") or repo.get("owner").get("nickname"),
            datetime.datetime.now().strftime("%Y%m%d%H%m%s"),
        )
    )
    debug("Cleaning up...", True)
    for d in os.listdir(location):
        path = os.path.join(location, d)
        if os.path.isdir(path):
            exec_cmd("rm -rfv %s" % path)


def fetch_lfs_content(backup_dir):
    debug("Fetching LFS content...")
    os.chdir(backup_dir)
    command = "git lfs fetch --all"
    exec_cmd(command, stop_on_error=False)


def get_repositories(method="GET", username=None, password=None, team=None, data=None):
    url = "https://api.bitbucket.org/2.0/repositories/{}/".format(team or username)

    header = "%s:%s" % (username, password)
    header = {
        "Authorization": "Basic %s"
        % (base64.b64encode(header.encode("utf_8")).decode("utf_8").strip())
    }
    request = Request(url, data, header)
    request.get_method = lambda: method
    result = urlopen(request).read().decode("utf-8")
    repos_data = json.loads(result)
    repos = []
    for repo in repos_data.get("values"):
        repos.append(repo)
    while repos_data.get("next"):
        request = Request(repos_data.get("next"), data, header)
        result = urlopen(request).read().decode("utf-8")
        repos_data = json.loads(result)
        for repo in repos_data.get("values"):
            repos.append(repo)
    return repos


def clone_repo(
    repo,
    backup_dir,
    http,
    username,
    password,
    mirror=False,
    with_wiki=False,
    fetch_lfs=False,
):
    global _quiet, _verbose
    scm = repo.get("scm")
    slug = repo.get("slug")
    owner = repo.get("owner").get("username") or repo.get("owner").get("nickname")
    owner_url = quote(owner)
    if http and not all((username, password)):
        exit("Cannot backup via http without username and password" % scm)
    slug_url = quote(slug)
    command = None
    if scm == "hg":
        if http:
            command = "hg clone https://%s:%s@bitbucket.org/%s/%s" % (
                quote(username),
                quote(password),
                owner_url,
                slug_url,
            )
        else:
            command = "hg clone ssh://hg@bitbucket.org/%s/%s" % (owner_url, slug_url)
    if scm == "git":
        git_command = "git clone"
        if mirror:
            git_command = "git clone --mirror"
        if http:
            command = "%s https://%s:%s@bitbucket.org/%s/%s.git" % (
                git_command,
                quote(username),
                quote(password),
                owner_url,
                slug_url,
            )
        else:
            command = "%s git@bitbucket.org:%s/%s.git" % (
                git_command,
                owner_url,
                slug_url,
            )
    if not command:
        exit("could not build command (scm [%s] not recognized?)" % scm)
    debug("Cloning %s..." % repo.get("name"))
    exec_cmd('%s "%s"' % (command, backup_dir))
    if scm == "git" and fetch_lfs:
        fetch_lfs_content(backup_dir)
    if with_wiki and repo.get("has_wiki"):
        debug("Cloning %s's Wiki..." % repo.get("name"))
        exec_cmd("%s/wiki %s_wiki" % (command, backup_dir))


def update_repo(repo, backup_dir, with_wiki=False, prune=False, fetch_lfs=False):
    scm = repo.get("scm")
    command = None
    os.chdir(backup_dir)
    if scm == "hg":
        command = "hg pull -u"
    if scm == "git":
        command = "git remote update"
        if prune:
            command = "%s %s" % (command, "--prune")
    if not command:
        exit("could not build command (scm [%s] not recognized?)" % scm)
    debug("Updating %s..." % repo.get("name"))
    exec_cmd(command)
    if scm == "git" and fetch_lfs:
        fetch_lfs_content(backup_dir)
    wiki_dir = "%s_wiki" % backup_dir
    if with_wiki and repo.get("has_wiki") and os.path.isdir(wiki_dir):
        os.chdir(wiki_dir)
        debug("Updating %s's Wiki..." % repo.get("name"))
        exec_cmd(command)


def main():
    parser = argparse.ArgumentParser(description="Usage: %prog [options] ")
    parser.add_argument("-u", "--username", dest="username", help="Bitbucket username")
    parser.add_argument("-p", "--password", dest="password", help="Bitbucket password")
    parser.add_argument("-t", "--team", dest="team", help="Bitbucket team")
    parser.add_argument(
        "-l", "--location", dest="location", help="Local backup location"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        help="Verbose output of all cloning commands",
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", dest="quiet", help="No output to stdout"
    )
    parser.add_argument(
        "-c",
        "--compress",
        action="store_true",
        dest="compress",
        help="Creates a compressed file with all cloned repositories (cleans up location directory)",
    )
    parser.add_argument(
        "-a",
        "--attempts",
        dest="attempts",
        type=int,
        default=1,
        help="max. number of attempts to backup repository",
    )
    parser.add_argument(
        "--mirror",
        action="store_true",
        help="Clone just bare repositories with git clone --mirror (git only)",
    )
    parser.add_argument(
        "--fetchlfs",
        action="store_true",
        help="Fetch LFS content after clone/pull (git only)",
    )
    parser.add_argument(
        "--with-wiki", dest="with_wiki", action="store_true", help="Includes wiki"
    )
    parser.add_argument(
        "--http", action="store_true", help="Fetch via https instead of SSH"
    )
    parser.add_argument(
        "--skip-password",
        dest="skip_password",
        action="store_true",
        help="Ignores password prompting if no password is provided (for public repositories)",
    )
    parser.add_argument(
        "--prune", dest="prune", action="store_true", help="Prune repo on remote update"
    )
    parser.add_argument(
        "--delete-extraneous", dest="delete_extraneous", action="store_true", help="Delete extraneous repositories from backup"
    )
    parser.add_argument(
        "--ignore-repo-list",
        dest="ignore_repo_list",
        nargs="+",
        type=str,
        help="specify list of repo slug names to skip",
    )
    args = parser.parse_args()
    location = args.location
    username = args.username
    password = args.password
    http = args.http
    max_attempts = args.attempts
    global _quiet
    _quiet = args.quiet
    global _verbose
    _verbose = args.verbose
    _mirror = args.mirror
    _fetchlfs = args.fetchlfs
    _with_wiki = args.with_wiki
    _delete_extraneous = args.delete_extraneous
    if _quiet:
        _verbose = False  # override in case both are selected
    team = args.team

    if not username:
        username = input("Enter bitbucket username: ")
    if not password:
        password = getpass(prompt="Enter your bitbucket password: ")
    if not location:
        location = input("Enter local location to backup to: ")
    location = os.path.abspath(location)

    # ok to proceed
    try:
        repos = get_repositories(username=username, password=password, team=team)
        repos = sorted(repos, key=lambda repo_: repo_.get("name"))
        dir_list = []
        if not repos:
            print(
                "No repositories found. Are you sure you provided the correct password"
            )
        for repo in repos:
            dir_list.append(repo.get("slug"))
            if repo.get('has_wiki'):
                dir_list.append(repo.get("slug") + "_wiki")

            if args.ignore_repo_list and repo.get("slug") in args.ignore_repo_list:
                debug(
                    "ignoring repo %s with slug: %s"
                    % (repo.get("name"), repo.get("slug"))
                )
                continue

            debug("Backing up [%s]..." % repo.get("name"), True)
            backup_dir = os.path.join(location, repo.get("slug"))

            for attempt in range(1, max_attempts + 1):
                try:
                    if not os.path.isdir(backup_dir):
                        clone_repo(
                            repo,
                            backup_dir,
                            http,
                            username,
                            password,
                            mirror=_mirror,
                            with_wiki=_with_wiki,
                            fetch_lfs=_fetchlfs,
                        )
                    else:
                        debug(
                            "Repository [%s] already in place, just updating..."
                            % repo.get("name")
                        )
                        update_repo(
                            repo,
                            backup_dir,
                            with_wiki=_with_wiki,
                            prune=args.prune,
                            fetch_lfs=_fetchlfs,
                        )
                except:
                    if attempt == max_attempts:
                        raise MaxBackupAttemptsReached(
                            "repo [%s] is reached maximum number [%d] of backup tries"
                            % (repo.get("name"), attempt)
                        )
                    debug(
                        "Failed to backup repository [%s], keep trying, %d attempts remain"
                        % (repo.get("name"), max_attempts - attempt)
                    )
                else:
                    break

        for dir in os.listdir(location):
            if _delete_extraneous and os.path.isdir(os.path.join(location, dir)) and not dir in dir_list:
                debug("Removing repository [%s]..." % dir, True)
                shutil.rmtree(os.path.join(location, dir))

        if args.compress:
            compress(repo, location)
        debug("Finished!", True)
    except HTTPError as err:
        if err.code == 401:
            exit(
                "Unauthorized! Check your credentials and try again.", 22
            )  # EINVAL - Invalid argument
        else:
            exit("Connection Error! Bitbucket returned HTTP error [%s]." % err.code)
    except URLError as e:
        exit(
            "Unable to reach Bitbucket: %s." % e.reason, 101
        )  # ENETUNREACH - Network is unreachable
    except (KeyboardInterrupt, SystemExit):
        exit(
            "Operation cancelled. There might be inconsistent data in location directory.",
            0,
        )
    except MaxBackupAttemptsReached as e:
        exit("Unable to backup: %s" % e)
    except:
        if not _quiet:
            import traceback

            traceback.print_exc()
        exit("Unknown error.", 11)  # EAGAIN - Try again


if __name__ == "__main__":
    main()
