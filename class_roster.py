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
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

def addStudentData(class_roster, students):
  class_roster['students'] = []
  for e in class_roster['emails']:
    for s in students:
      if (s['email'].lower() == e):
        class_roster['students'].append(s)

class ClassRoster(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, class_id, message):
    self.redirect("/class_roster?%s" % urllib.urlencode(
        {'message': message,
         'institution': institution,
         'session': session,
         'class_id': class_id}))

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
    class_id = self.request.get("class_id")
    if not class_id:
      logging.fatal("no class_id")
    action = self.request.get("action")
    if not action:
      logging.fatal("no action")

    if action == "remove student":
      email = self.request.get("email")
      logic.RemoveStudentFromClass(institution, session, email, class_id)
      self.RedirectToSelf(institution, session, class_id, "removed %s" % email)

    if action == "run lottery":
      cid = self.request.get("cid")
      if not cid:
        logging.fatal("no class id")
      candidates = self.request.get("candidates")
      candidates = candidates.split(",")
      logic.RunLottery(institution, session, cid, candidates)
      self.RedirectToSelf(institution, session, cid, "lottery %s" % cid)

    self.RedirectToSelf(institution, session, class_id, "Unknown action")

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
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'class_roster': class_roster,
      'students': students,
      'class_details': class_details
    }
    template = JINJA_ENVIRONMENT.get_template('class_roster.html')
    self.response.write(template.render(template_values))
