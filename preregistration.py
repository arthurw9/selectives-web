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


class Preregistration(webapp2.RequestHandler):
  def get(self):
    auth = authorizer.Authorizer(self)
    if not auth.HasStudentAccess():
      auth.Redirect()
      return

    institution = self.request.get("institution")
    if not institution:
      logging.fatal("no institution")
    session = self.request.get("session")
    if not session:
      logging.fatal("no session")
    if not auth.HasPageAccess(institution, session, "materials"):
      auth.RedirectTemporary(institution, session)
      return

    message = self.request.get('message')
    session_query = urllib.urlencode({'institution': institution,
                                      'session': session})
    view_links = models.Links.FetchJson(institution, session)
    if not view_links:
      view_links = ''

    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'view_links': view_links,
      'self': self.request.uri,
    }
    template = JINJA_ENVIRONMENT.get_template('preregistration.html')
    self.response.write(template.render(template_values))
