import os
import urllib
import jinja2
import webapp2
import logging
import yaml
import itertools
import random
import error_check_logic
import models
import authorizer
import logic

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class Impersonation(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/impersonation?%s" % urllib.urlencode(
        {'message': message, 
         'institution': institution,
         'session': session}))

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

    setup_status = error_check_logic.Checker.getStatus(institution, session)
    students = models.Students.FetchJson(institution, session)
    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'setup_status': setup_status,
      'session_query': session_query,
      'students': students,
    }
    template = JINJA_ENVIRONMENT.get_template('impersonation.html')
    self.response.write(template.render(template_values))
