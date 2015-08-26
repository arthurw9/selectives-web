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


class Dayparts(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/dayparts?%s" % urllib.urlencode(
        {'message': message, 
         'institution': institution,
         'session': session}))

  def post(self):
    auth = authorizer.Authorizer()
    if auth.ShouldRedirect(self):
      auth.Redirect(self)
      return

    institution = self.request.get("institution")
    if not institution:
      logging.fatal("no institution")
    session = self.request.get("session")
    if not session:
      logging.fatal("no session")
    dayparts = self.request.get("dayparts")
    if not session:
      logging.fatal("no dayparts")
    models.Dayparts.store(institution, session, dayparts)
    self.RedirectToSelf(institution, session, "saved dayparts")

  def get(self):
    auth = authorizer.Authorizer()
    if auth.ShouldRedirect(self):
      auth.Redirect(self)
      return

    institution = self.request.get("institution")
    if not institution:
      logging.fatal("no institution")
    session = self.request.get("session")
    if not session:
      logging.fatal("no session")

    logout_url = auth.GetLogoutUrl(self)
    message = self.request.get('message')
    session_query = urllib.urlencode({'institution': institution,
                                      'session': session})
    dayparts = models.Dayparts.fetch(institution, session)
    if not dayparts:
      dayparts = """
        # sample data (with no # signs)
        # - monday am
        # - Tuesday pm"""

    template_values = {
      'logout_url': logout_url,
      'user' : auth.user,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'dayparts': dayparts,
      'self': self.request.uri,
    }
    template = JINJA_ENVIRONMENT.get_template('dayparts.html')
    self.response.write(template.render(template_values))


application = webapp2.WSGIApplication([
  ('/dayparts', Dayparts),
], debug=True)
