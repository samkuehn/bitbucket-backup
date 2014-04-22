#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Bitbucket API wrapper.  Written to be somewhat like py-github:

https://github.com/dustin/py-github

"""

try:
    from urllib.request import Request, urlopen
except ImportError:
    from urllib2 import Request, urlopen
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode
from functools import wraps
import datetime
import time
import base64

try:
    import json
except ImportError:
    import simplejson as json

__all__ = ['AuthenticationRequired', 'to_datetime', 'BitBucket']

api_toplevel = 'https://api.bitbucket.org/'
api_base = '%s1.0/' % api_toplevel


class AuthenticationRequired(Exception):
    pass


def requires_authentication(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        username = self.bb.username if hasattr(self, 'bb') else self.username
        password = self.bb.password if hasattr(self, 'bb') else self.password
        if not all((username, password)):
            raise AuthenticationRequired("%s requires authentication" % method.__name__)
        return method(self, *args, **kwargs)
    return wrapper


def smart_encode(**kwargs):
    """Urlencode's provided keyword arguments.  If any kwargs are None, it does
    not include those."""
    args = dict(kwargs)
    for k, v in args.items():
        if v is None:
            del args[k]
    if not args:
        return ''
    return urlencode(args)


def to_datetime(timestring):
    """Convert one of the bitbucket API's timestamps to a datetime object."""
    format = '%Y-%m-%d %H:%M:%S'
    timestring = timestring.split('+')[0].strip()
    return datetime.datetime(*time.strptime(timestring, format)[:7])


class BitBucket(object):

    """Main bitbucket class.  Use an instantiated version of this class
    to make calls against the REST API."""

    def __init__(self, username='', password='', verbose=False):
        self.username = username
        self.password = password
        self.verbose = verbose

    def build_request(self, url, method="GET", data=None):
        if not all((self.username, self.password)):
            return Request(url)
        auth = '%s:%s' % (self.username, self.password)
        auth = {'Authorization': 'Basic %s' % (base64.b64encode(auth.encode("utf_8")).decode("utf_8").strip())}
        request = Request(url, data, auth)
        request.get_method = lambda: method
        return request

    def load_url(self, url, method="GET", data=None):
        if self.verbose:
            print("Sending request to: [{0}]".format(url))
        request = self.build_request(url, method=method, data=data)
        result = urlopen(request).read()
        if self.verbose:
            print("Response data: [{0}]".format(result))
        return result

    def user(self, username):
        return User(self, username)

    def repository(self, username, slug):
        return Repository(self, username, slug)

    @requires_authentication
    def emails(self):
        """Returns a list of configured email addresses for the authenticated user."""
        url = api_base + 'emails/'
        return json.loads(self.load_url(url))

    @requires_authentication
    def create_repo(self, repo_data):
        url = api_base + 'repositories/'
        return json.loads(self.load_url(url, method="POST", data=urlencode(repo_data)))

    def __repr__(self):
        extra = ''
        if all((self.username, self.password)):
            extra = ' (auth: %s)' % self.username
        return '<BitBucket API%s>' % extra


class User(object):

    """API encapsulation for user related bitbucket queries."""

    def __init__(self, bb, username):
        self.bb = bb
        self.username = username

    def repository(self, slug):
        return Repository(self.bb, self.username, slug)

    def repositories(self):
        user_data = self.get()
        return user_data['repositories']

    def events(self, start=None, limit=None):
        query = smart_encode(start=start, limit=limit)
        url = api_base + 'users/%s/events/' % self.username
        if query:
            url += '?%s' % query
        return json.loads(self.bb.load_url(url))

    def get(self):
        url = api_base + 'users/%s/' % self.username
        return json.loads(self.bb.load_url(url).decode('utf-8'))

    def __repr__(self):
        return '<User: %s>' % self.username


class Repository(object):

    def __init__(self, bb, username, slug):
        self.bb = bb
        self.username = username
        self.slug = slug
        self.base_url = api_base + 'repositories/%s/%s/' % (self.username, self.slug)

    def get(self):
        return json.loads(self.bb.load_url(self.base_url).decode('utf-8'))

    def changeset(self, revision):
        """Get one changeset from a repos."""
        url = self.base_url + 'changesets/%s/' % (revision)
        return json.loads(self.bb.load_url(url))

    def changesets(self, limit=None):
        """Get information about changesets on a repository."""
        url = self.base_url + 'changesets/'
        query = smart_encode(limit=limit)
        if query:
            url += '?%s' % query
        return json.loads(self.bb.load_url(url))

    def tags(self):
        """Get a list of tags for a repository."""
        url = self.base_url + 'tags/'
        return json.loads(self.bb.load_url(url))

    def branches(self):
        """Get a list of branches for a repository."""
        url = self.base_url + 'branches/'
        return json.loads(self.bb.load_url(url))

    def issue(self, number):
        return Issue(self.bb, self.username, self.slug, number)

    def issues(self, start=None, limit=None):
        url = self.base_url + 'issues/'
        query = smart_encode(start=start, limit=limit)
        if query:
            url += '?%s' % query
        return json.loads(self.bb.load_url(url))

    def events(self):
        url = self.base_url + 'events/'
        return json.loads(self.bb.load_url(url))

    def followers(self):
        url = self.base_url + 'followers/'
        return json.loads(self.bb.load_url(url))

    @requires_authentication
    def save(self, repo_data):
        url = self.base_url
        return json.loads(self.bb.load_url(url, method="PUT", data=urlencode(repo_data)))

    def __repr__(self):
        return '<Repository: %s\'s %s>' % (self.username, self.slug)


class Issue(object):

    def __init__(self, bb, username, slug, number):
        self.bb = bb
        self.username = username
        self.slug = slug
        self.number = number
        self.base_url = api_base + 'repositories/%s/%s/issues/%s/' % (username, slug, number)

    def get(self):
        return json.loads(self.bb.load_url(self.base_url).decode('utf-8'))

    def followers(self):
        url = self.base_url + 'followers/'
        return json.loads(self.bb.load_url(url))

    def __repr__(self):
        return '<Issue #%s on %s\'s %s>' % (self.number, self.username, self.slug)
