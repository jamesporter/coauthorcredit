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


def get_encoded_auth():
    return base64.b64encode("%s:%s" % (dbx_keys.keys["app_key"], dbx_keys.keys["app_secret"]))


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + "/templates/"))

#jinja_environment.filters['datetime'] =

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

                self.response.out.write("Welcome %s" % userModel.name)
        else:
            self.response.out.write("Unable to connect to Dropbox")

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/dbxauth', AuthHandler),
    ('/webhook', HooksHandler),
], debug=True)
