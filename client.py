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
import base64

try:
    import json
except ImportError:
    import simplejson as json


def get_repositories(method="GET", username=None, password=None, team=None, data=None):
    url = "https://api.bitbucket.org/2.0/repositories/{}/".format(team or username)

    header = "%s:%s" % (username, password)
    header = {
        "Authorization": "Basic %s"
        % (base64.b64encode(header.encode("utf_8")).decode("utf_8").strip())
    }
    request = Request(url, data, header)
    request.get_method = lambda: method
    result = urlopen(request).read()
    repos_data = json.loads(result)
    repos = []
    for repo in repos_data.get("values"):
        repos.append(repo)
    while repos_data.get("next"):
        request = Request(url, data, header)
        result = urlopen(request).read()
        repos_data = json.loads(result)
        for repo in repos_data.get("values"):
            repos.append(repo)
    return repos
