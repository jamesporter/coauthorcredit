#!/usr/bin/env python

import webapp2
import jinja2
import os
from google.appengine.api import users
import dbx_keys

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
        template = jinja_environment.get_template("index.html")
        self.response.out.write(template.render({}))


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
    pass


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/dbxauth', AuthHandler),
    ('/webhook', HooksHandler),
], debug=True)
