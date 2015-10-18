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


class PreferencesAdmin(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/preferences_admin?%s" % urllib.urlencode(
        {'message': message, 
         'institution': institution,
         'session': session}))

  def ClearPrefs(self, institution, session):
    students = models.Students.fetch(institution, session)
    students = yaml.load(students)
    classes = models.Classes.Fetch(institution, session)
    classes = yaml.load(classes)
    for student in students:
      email = student['email']
      #TODO find the list of eligible classes for each student
      models.Preferences.Store(email, institution, session,
                               [], [], [])

  def RandomPrefs(self, institution, session):
    students = models.Students.fetch(institution, session)
    students = yaml.load(students)
    classes = models.Classes.Fetch(institution, session)
    classes = yaml.load(classes)
    for student in students:
      email = student['email']
      eligible_class_ids = logic.EligibleClassIdsForStudent(student, classes)
      eligible_class_ids = set(eligible_class_ids)
      want = random.sample(eligible_class_ids, random.randint(1,5))
      dontwant = random.sample(eligible_class_ids.difference(want), random.randint(1,5))
      # want = [str(item) for item in want]
      # dontwant = [str(item) for item in dontwant]
      models.Preferences.Store(email, institution, session,
                               want, [], dontwant)

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
    action = self.request.get("action")
    if action == "Clear Prefs":
      self.ClearPrefs(institution, session)
    if action == "Random Prefs":
      self.RandomPrefs(institution, session)
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
