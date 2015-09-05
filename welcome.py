import os
import urllib
import jinja2
import webapp2
import logging
import models
import authorizer

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class Welcome(webapp2.RequestHandler):

  def get(self):
    auth = authorizer.Authorizer(self)
    logout_url = auth.GetLogoutUrl(self)

    template_values = {
      'logout_url': logout_url,
      'user' : auth.user,
    }
    template = JINJA_ENVIRONMENT.get_template('welcome.html')
    self.response.write(template.render(template_values))


application = webapp2.WSGIApplication([
  ('/welcome', Welcome),
], debug=True)
