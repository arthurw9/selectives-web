import os
import urllib
import jinja2
import webapp2
import logging
import yaml
import models
import authorizer

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class Verification(webapp2.RequestHandler):

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

    student_info = auth.GetStudentInfo(institution, session)

    logout_url = auth.GetLogoutUrl(self)
    template_values = {
      'logout_url': logout_url,
      'user' : auth.user,
      'institution' : institution,
      'session' : session,
      'student_name': student_info['name'],
      'current_grade': student_info['current_grade'],
    }
    template = JINJA_ENVIRONMENT.get_template('verification.html')
    self.response.write(template.render(template_values))
