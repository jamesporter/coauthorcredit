#!/usr/bin/env python

import webapp2
import jinja2
import os
from google.appengine.api import users
import dbx_keys
import models

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
                "redirect_uri":self.request.url.replace("http", "https") + "dbxauth",
                "csrf":userModel.code
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


class AuthHandler(webapp2.RequestHandler):
    def get(self):
        dbxCode = self.request.get('code')
        dbxState = self.request.get('state')
        #TODO check state matched the user's CSRF token...




        self.response.out.write("Auth Response")


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/dbxauth', AuthHandler),
    ('/webhook', HooksHandler),
], debug=True)
