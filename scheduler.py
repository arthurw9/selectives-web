import jinja2
import logging
import os
import urllib
import webapp2
import yaml
import random

import authorizer
import models
import logic

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

  def ClearPrefs(self, institution, session):
    students = models.Students.FetchJson(institution, session)
    classes = models.Classes.FetchJson(institution, session)
    for student in students:
      email = student['email']
      #TODO find the list of eligible classes for each student
      models.Preferences.Store(email, institution, session,
                               [], [], [])

  def RandomPrefs(self, institution, session):
    students = models.Students.FetchJson(institution, session)
    classes = models.Classes.FetchJson(institution, session)
    for student in students:
      email = student['email']
      eligible_class_ids = logic.EligibleClassIdsForStudent(
          institution, session, student, classes)
      eligible_class_ids = set(eligible_class_ids)
      want = random.sample(eligible_class_ids, random.randint(1,5))
      dontwant = random.sample(eligible_class_ids.difference(want), random.randint(1,5))
      # want = [str(item) for item in want]
      # dontwant = [str(item) for item in dontwant]
      models.Preferences.Store(email, institution, session,
                               want, [], dontwant)

  def ClearAllSchedules(self, institution, session):
    students = models.Students.FetchJson(institution, session)
    for student in students:
      empty_class_ids = ''
      models.Schedule.Store(institution, session,
                            student['email'].lower(),
                            empty_class_ids)
    classes = models.Classes.FetchJson(institution, session)
    for class_obj in classes:
      no_student_emails = ""
      models.ClassRoster.Store(institution, session,
                               class_obj,
                               no_student_emails)

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
    action = self.request.get("action")
    if action == "Clear Prefs":
      self.ClearPrefs(institution, session)
    if action == "Random Prefs":
      self.RandomPrefs(institution, session)
    if action == "Clear Schedules":
      self.ClearAllSchedules(institution, session)
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

    message = self.request.get('message')
    session_query = urllib.urlencode({'institution': institution,
                                      'session': session})

    num_students = len(models.Students.FetchJson(institution, session))
    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'self': self.request.uri,
      'num_students': num_students,
    }
    template = JINJA_ENVIRONMENT.get_template('scheduler.html')
    self.response.write(template.render(template_values))
