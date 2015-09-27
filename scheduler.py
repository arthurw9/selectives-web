import jinja2
import logging
import os
import urllib
import webapp2
import yaml

import authorizer
import models

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class Scheduler(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/scheduler?%s" % urllib.urlencode(
        {'message': message, 
         'institution': institution,
         'session': session}))

  def post(self):
    auth = authorizer.Authorizer(self)
    if not auth.CanAdministerInstitutionFromUrl():
      auth.Redirect()
      return

    institution = self.request.get("institution")
    if not institution:
      logging.fatal("no institution")
    session = self.request.get("session")
    if not session:
      logging.fatal("no session")
    #TODO is there anything to do here?
    self.RedirectToSelf(institution, session, "saved classes")

  def get(self):
    auth = authorizer.Authorizer(self)
    if not auth.CanAdministerInstitutionFromUrl():
      auth.Redirect()
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

    num_students = len(yaml.load(models.Students.fetch(institution, session)))
    template_values = {
      'logout_url': logout_url,
      'user' : auth.user,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'self': self.request.uri,
      'num_students': num_students,
    }
    template = JINJA_ENVIRONMENT.get_template('scheduler.html')
    self.response.write(template.render(template_values))
