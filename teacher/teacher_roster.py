import os
import urllib
import jinja2
import webapp2
import logging
import yaml
import itertools
import random

import models
import authorizer
import logic

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(os.path.dirname(__file__))),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

def addStudentData(class_roster, students):
  class_roster['students'] = []
  for e in class_roster['emails']:
    for s in students:
      if (s['email'] == e):
        class_roster['students'].append(s)

class TeacherRoster(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/teacher_roster?%s" % urllib.urlencode(
        {'message': message,
         'institution': institution,
         'session': session,}))

  def post(self):
    auth = authorizer.Authorizer(self)
    if not auth.HasTeacherAccess():
      auth.Redirect()
      return

    institution = self.request.get("institution")
    if not institution:
      logging.fatal("no institution")
    session = self.request.get("session")
    if not session:
      logging.fatal("no session")

    self.RedirectToSelf(institution, session, "Unknown action")

  def get(self):
    auth = authorizer.Authorizer(self)
    if not auth.HasTeacherAccess():
      auth.Redirect()
      return

    institution = self.request.get("institution")
    if not institution:
      logging.fatal("no institution")
    session = self.request.get("session")
    if not session:
      logging.fatal("no session")
    class_id = self.request.get("class_id")
    if not session:
      logging.fatal("no class id")

    message = self.request.get('message')
    session_query = urllib.urlencode({'institution': institution,
                                      'session': session})

    class_roster = models.ClassRoster.FetchEntity(institution, session, class_id)
    class_roster['emails'].sort()
    students = models.Students.FetchJson(institution, session)
    addStudentData(class_roster, students)
    classes = models.Classes.FetchJson(institution, session)
    class_details = ''
    for c in classes:
      if (str(c['id']) == class_id):
        class_details = c
        break
    template_values = {
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'class_roster': class_roster,
      'class_details': class_details
    }
    template = JINJA_ENVIRONMENT.get_template('teacher/teacher_roster.html')
    self.response.write(template.render(template_values))
