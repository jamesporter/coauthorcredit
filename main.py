#!/usr/bin/env python

import webapp2
import jinja2
import os
from google.appengine.api import users
import dbx_keys
import base64
import models
from google.appengine.api import urlfetch
import urllib
import json
from collections import defaultdict


def get_encoded_auth():
    return base64.b64encode("%s:%s" % (dbx_keys.keys["app_key"], dbx_keys.keys["app_secret"]))


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + "/templates/"))

jinja_environment.filters['escape'] = urllib.quote

# Can do things like:
# user = users.get_current_user()
# if not user:
#
# else:
#     userModel = models.UserRecord.get_and_create(user)


class MainHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url("/"))
        else:
            userModel = models.UserRecord.get_and_create(user)
            template = jinja_environment.get_template("index.html")


            #Note must be https redirect url (hence replacing http if in url)
            self.response.out.write(template.render({
                "app_key":dbx_keys.keys["app_key"],
                "redirect_uri":self.request.url.replace("http://", "https://") + "dbxauth",
                "csrf":userModel.code,
                "authorized": userModel.authorized,
                "name": userModel.name
            }))


class HooksHandler(webapp2.RequestHandler):
    def get(self):
        """Respond to the webhook verification (GET request) by echoing back the challenge parameter."""
        self.response.out.write(self.request.get('challenge'))

    def post(self):
        """The webhook message: should have a json body which looks like:
        {
           "delta": {
                "users": [
                    12345678,
                    23456789,
                    ...
                ]
            }
        }

        should then call /delta (in core Dbx API) with a path prefix
        """
        pass


def post_dbx_token(code):
    token_url = "https://api.dropbox.com/1/oauth2/token"
    payload = {
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": "https://coauthorcredit.appspot.com/dbxauth"
    }
    result = urlfetch.fetch(url=token_url,
                            payload=urllib.urlencode(payload),
                            method=urlfetch.POST,
                            headers={'Content-Type': 'application/x-www-form-urlencoded',
                                     "Authorization": "Basic %s" % get_encoded_auth()})

    #Result is like (when successful):
    # result.content = {"access_token": "YNHyiBlw7vAAAAAAAAALE5CLFv1S7at70jmhpNH-qVo82sSlmAG7qOH0IOdcoebV", "token_type": "bearer", "uid": "63235995"}'
    # result.status_code: 200
    # result.headers = {'via': 'HTTP/1.1 GWA', 'set-cookie': 'gvc=MjUxNjIzOTQzMjU1MTE2Mjc4ODc2NzgxODExODE5NzcxNTM5ODU2; expires=Thu, 23 Jan 2020 13:02:11 GMT; Path=/; httponly', 'x-google-cache-control': 'remote-fetch', 'x-server-response-time': '301', 'server': 'nginx', 'date': 'Sat, 24 Jan 2015 13:02:11 GMT', 'connection': 'keep-alive', 'x-dropbox-request-id': 'eec75ddd4d5889c9796b4b16ea141794', 'pragma': 'no-cache', 'cache-control': 'no-cache', 'x-dropbox-http-protocol': 'None', 'x-frame-options': 'SAMEORIGIN', 'content-type': 'text/javascript'}

    result.content = json.loads(result.content)
    return result


def get_dbx_user_info(authToken):
    userResult = urlfetch.fetch(url="https://api.dropbox.com/1/account/info",

                                            headers={"Authorization" : "Bearer %s" % authToken})
    userResult.content = json.loads(userResult.content)
    return userResult


def get_metadata_for_path(authToken, path):
    result = urlfetch.fetch(url="https://api.dropbox.com/1/metadata/auto/" + urllib.quote(path) + "?list=true",
                            headers={"Authorization" : "Bearer %s" % authToken})

    #Should get:
    # {
    #     "size": "0 bytes",
    #     "hash": "37eb1ba1849d4b0fb0b28caf7ef3af52",
    #     "bytes": 0,
    #     "thumb_exists": false,
    #     "rev": "714f029684fe",
    #     "modified": "Wed, 27 Apr 2011 22:18:51 +0000",
    #     "path": "/Photos",
    #     "is_dir": true,
    #     "icon": "folder",
    #     "root": "dropbox",
    #     "contents": [
    #         {
    #             "size": "2.3 MB",
    #             "rev": "38af1b183490",
    #             "thumb_exists": true,
    #             "bytes": 2453963,
    #             "modified": "Mon, 07 Apr 2014 23:13:16 +0000",
    #             "client_mtime": "Thu, 29 Aug 2013 01:12:02 +0000",
    #             "path": "/Photos/flower.jpg",
    #             "photo_info": {
    #               "lat_long": [
    #                 37.77256666666666,
    #                 -122.45934166666667
    #               ],
    #               "time_taken": "Wed, 28 Aug 2013 18:12:02 +0000"
    #             },
    #             "is_dir": false,
    #             "icon": "page_white_picture",
    #             "root": "dropbox",
    #             "mime_type": "image/jpeg",
    #             "revision": 14511
    #         }
    #     ],
    #     "revision": 29007
    # }
    jc = json.loads(result.content)

    if "contents" in jc:
        contentsList = jc["contents"]
        info = []
        for item in contentsList:
            if item['is_dir']:
                pass #for now we ignore, should add a link to this?
            else:
                info.append(item)
        return info
    else:
        print jc
        return []


def get_revisions_for_file(authToken, filePath):
    result = urlfetch.fetch(url="https://api.dropbox.com/1/revisions/auto/" + filePath,
                            headers={"Authorization" : "Bearer %s" % authToken})

    #Should get:
    # [
    #     {
    #         "is_deleted": true,
    #         "revision": 4,
    #         "rev": "40000000d",
    #         "thumb_exists": false,
    #         "bytes": 0,
    #         "modified": "Wed, 20 Jul 2011 22:41:09 +0000",
    #         "path": "/hi2",
    #         "is_dir": false,
    #         "icon": "page_white",
    #         "root": "app_folder",
    #         "mime_type": "application/octet-stream",
    #         "size": "0 bytes"
    #     },
    #     {
    #         "revision": 1,
    #         "rev": "10000000d",
    #         "thumb_exists": false,
    #         "bytes": 3,
    #         "modified": "Wed, 20 Jul 2011 22:40:43 +0000",
    #         "path": "/hi2",
    #         "is_dir": false,
    #         "icon": "page_white",
    #         "root": "app_folder",
    #         "mime_type": "application/octet-stream",
    #         "size": "3 bytes"
    #     }
    # ]

    # Should also have a modifier	For files within a shared folder,
    # this field specifies which user last modified this file.
    # The value is a user dictionary with the fields uid (user ID), display_name,
    # and, if the linked account is a member of a Dropbox for Business team, same_team
    # (whether the user is on the same team as the linked account). If this endpoint
    # is called by a Dropbox for Business app and the user is on that team, a
    # member_id field will also be present in the user dictionary. If the modifying
    # user no longer exists, the value will be null.



    jr = json.loads(result.content)
    print "Got %d revisions" % len(jr)
    return jr




class AuthHandler(webapp2.RequestHandler):
    def get(self):
        dbxCode = self.request.get('code')
        dbxState = self.request.get('state')
        #TODO check state matched the user's CSRF token...

        result = post_dbx_token(dbxCode)

        if "access_token" in result.content:
            user = users.get_current_user()
            if not user:
                self.redirect(users.create_login_url("/"))
            else:
                userModel = models.UserRecord.get_and_create(user)
                userModel.add_dbx_details(result.content['uid'], result.content['access_token'])
                userResult = get_dbx_user_info(userModel.dbxCode)

                userModel.authorized = True
                userModel.name = userResult.content["display_name"]
                userModel.put()

                self.redirect("/")
        else:
            self.response.out.write("Unable to connect to Dropbox")


class OpenHandler(webapp2.RequestHandler):
    def get(self, path):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url("/"))
        else:
            userModel = models.UserRecord.get_and_create(user)
            if userModel.authorized:
                fileList = get_metadata_for_path(userModel.dbxCode, path)
                template = jinja_environment.get_template("openFolder.html")
                self.response.out.write(template.render({"fileList": fileList, "path": path}))


def build_leaderboard(revisions):
    points = {}
    size = 0
    sr = sorted(revisions, key=lambda itm: itm["revision"])
    for item in sr:
        #This will crash if not a shared folder (and thus don't have modifier... should check)
        name = item["modifier"]["display_name"]
        if name in points:
            points[name] += (item["bytes"] - size)
        else:
            points[name] = (item["bytes"] - size)
        size = item["bytes"]

    leaderboard = []
    for k,v in points.iteritems():
        leaderboard.append({
            "name": k, "score":v
        })
    return sorted(leaderboard, key=lambda itm: itm["score"], reverse=True)


class ResultsHandler(webapp2.RequestHandler):
    def get(self, filePath):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url("/"))
        else:
            userModel = models.UserRecord.get_and_create(user)
            if userModel.authorized:
                revisionList = get_revisions_for_file(userModel.dbxCode, urllib.quote(filePath))
                leaderboard = build_leaderboard(revisionList)

                print(leaderboard)
                template = jinja_environment.get_template("results.html")
                self.response.out.write(template.render({"leaderboard": leaderboard, "filePath": filePath}))




app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/open/(.+)', OpenHandler),
    ('/results/(.+)', ResultsHandler),
    ('/dbxauth', AuthHandler),
    ('/webhook', HooksHandler),
], debug=True)
