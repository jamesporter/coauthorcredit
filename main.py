#!/usr/bin/env python

import webapp2
import jinja2
import os

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + "/templates/"))

#jinja_environment.filters['datetime'] =

class MainHandler(webapp2.RequestHandler):
    def get(self):
        template = jinja_environment.get_template("index.html")
        self.response.out.write(template.render({}))


class HooksHandler(webapp2.RequestHandler):
    def get(self):
        """Respond to the webhook verification (GET request) by echoing back the challenge parameter."""
        self.response.out.write(self.request.args.get('challenge'))


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/webhook', HooksHandler),
], debug=True)
