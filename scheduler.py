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

  def AutoRegister(self, institution, session):
    auto_register = models.AutoRegister.FetchJson(institution, session)
    students = models.Students.FetchJson(institution, session)
    for auto_class in auto_register:
      class_id = str(auto_class['class_id'])
      if (auto_class['applies_to'] == []): # applies to all students
        for s in students:
          if not ('exempt' in auto_class and s['email'] in auto_class['exempt']):
            logic.AddStudentToClass(institution, session, s['email'], class_id)
      for grp in auto_class['applies_to']:
        if 'current_grade' in grp:
          for s in students:
            if (s['current_grade'] == grp['current_grade']):
              if not ('exempt' in auto_class and s['email'] in auto_class['exempt']):
                logic.AddStudentToClass(institution, session, s['email'].lower(), class_id)
        if 'group' in grp:
          student_groups = models.GroupsStudents.FetchJson(institution, session)
          for sg in student_groups:
            if (sg['group_name'] == grp['group']):
              for s_email in sg['emails']:
                if not ('exempt' in auto_class and s_email in auto_class['exempt']):
                  logic.AddStudentToClass(institution, session, s_email.lower(), class_id)
        if 'email' in grp:
          # We have no way to prevent an exempt field here, so we should check for it.
          # But there really is no point to an exempt field when applies_to is email.
          if not ('exempt' in auto_class and grp['email'] in auto_class['exempt']):
            logic.AddStudentToClass(institution, session, grp['email'].lower(), class_id)

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
    if action == "Add Auto":
      self.AutoRegister(institution, session)
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
