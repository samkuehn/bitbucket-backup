#!/usr/bin/env python
import bitbucket
import os
import optparse

def clone_repo(repo, backup_dir, password):
    scm = repo.get('scm')
    slug = repo.get('slug')
    username = repo.get('owner')
    command = None
    if scm == 'hg':
        #command = 'hg clone https://%s:%s@bitbucket.org/%s/%s %s' % (username, password, username, slug, backup_dir)
        command = 'hg clone ssh://hg@bitbucket.org/%s/%s %s' % (username, slug, backup_dir)
    if scm == 'git':
        #command = "git clone https://%s:%s@bitbucket.org/%s/%s.git %s" % (username, password, username, slug, backup_dir)
        command = "git clone git@bitbucket.org:%s/%s.git %s" % (username, slug, backup_dir)
    if not command:
        return
    os.system(command)


def update_repo(repo, backup_dir, password):
    scm = repo.get('scm')
    slug = repo.get('slug')
    username = repo.get('owner')
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
    parser = optparse.OptionParser("Usage: %prog [options] ")
    parser.add_option("-u", "--username", dest="username", type="string", help="Bitbucket username")
    parser.add_option("-p", "--password", dest="password", type="string", help="Bitbucket password")
    parser.add_option("-l", "--location", dest="location", type="string", help="Local backup location")
    (options, args) = parser.parse_args()
    username = options.username
    password = options.password
    location = options.location
    if not username or not password or not location:
        parser.error('Please supply a username, password and backup location (-u <username> -p <password> -l <backup location>)')
    if not os.path.isdir(location):
        print "Backup location does not exist.  Please provide an existing directory."
    bb = bitbucket.BitBucket(username, password)
    user = bb.user(username)
    repos = user.repositories()
    for repo in repos:
        print "Backing up %s" % repo.get("name")
        backup_dir = os.path.join(location, repo.get("slug"))
        if not os.path.isdir(backup_dir):
            clone_repo(repo, backup_dir, password)
        else:
            update_repo(repo, backup_dir, password)