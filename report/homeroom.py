import os
import urllib
import jinja2
import webapp2
import logging
from sets import Set

import models
import authorizer

# Since we are inside the report directory, but Jinja doesn't allow
# {% extends '../menu.html' %}, call os.path.dirname(os.path.dirname())
# to go up to the parent directory.
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(os.path.dirname(__file__))),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

def getStudentsByHomeroom(students):
  by_homeroom = {}
  for s in students:
    if s['current_homeroom'] in by_homeroom:
      by_homeroom[s['current_homeroom']].append(s)
    else:
      by_homeroom[s['current_homeroom']] = [s]
  return by_homeroom

class Homeroom(webapp2.RequestHandler):
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

    students = models.Students.FetchJson(institution, session)
    if students:
      students.sort(key=lambda(s): (s['last'], s['first']))
    homerooms = getStudentsByHomeroom(students)

    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'homerooms': homerooms,
    }
    template = JINJA_ENVIRONMENT.get_template('report/homeroom.html')
    self.response.write(template.render(template_values))