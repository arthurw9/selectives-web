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


class Parser(object):

  def __init__(self, students):
    self.string = students
    self.yaml = yaml.load(students.lower())
    logging.info("students yaml = %s", str(self.yaml))

  def isValid(self):
    if self.yaml == None:
      sample = '\n'.join([
          "# Sample data:",
          "- email: foo@gmail.com",
          "  current_grade: 8",
          "- email: bar@gmail.com",
          "  current_grade: 7",])
      self.string = sample
      return False
    if not isinstance(self.yaml, list):
      err_msg = "# Students should be a list not %s\n" % type(self.yaml)
      self.string = err_msg + self.string
      return False
    for d in self.yaml:
      if not isinstance(d, dict):
        err_msg = "# %s should contain email and current grade.\n" % d
        self.string = err_msg + self.string
        return False
    return True

  def normalize(self):
    if self.isValid():
      return yaml.dump(self.yaml, default_flow_style=False)
    else:
      return self.string


class Students(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/students?%s" % urllib.urlencode(
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
    students = self.request.get("students")
    if not students:
      logging.warning("no students")
    students = Parser(students).normalize()
    logging.info("posted students %s", students)
    models.Students.store(institution, session, students)
    self.RedirectToSelf(institution, session, "saved students")

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
    students = models.Students.fetch(institution, session)

    template_values = {
      'logout_url': logout_url,
      'user' : auth.user,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'students': students,
      'self': self.request.uri,
    }
    template = JINJA_ENVIRONMENT.get_template('students.html')
    self.response.write(template.render(template_values))


application = webapp2.WSGIApplication([
  ('/students', Students),
], debug=True)
