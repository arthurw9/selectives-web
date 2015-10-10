import os
import urllib
import jinja2
import webapp2
import logging
import yaml
import itertools

import models
import authorizer

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class PreferencesAdmin(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/preferences_admin?%s" % urllib.urlencode(
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
    email = auth.user.email()
    self.RedirectToSelf(institution, session, "Saved Preferences")

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

    message = self.request.get('message')
    session_query = urllib.urlencode({'institution': institution,
                                      'session': session})

    students = models.Students.fetch(institution, session)
    students = yaml.load(students)
    template_values = {
      'logout_url': auth.GetLogoutUrl(self),
      'user' : auth.user,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'students': students,
    }
    template = JINJA_ENVIRONMENT.get_template('preferences_admin.html')
    self.response.write(template.render(template_values))
