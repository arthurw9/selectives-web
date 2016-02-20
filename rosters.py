import os
import urllib
import jinja2
import webapp2
import logging
import csv
import StringIO

import yayv
import schemas
import error_check_logic
import models
import authorizer

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

def studentFullName(students, email):
  for s in students:
    if s['email'].lower().strip() == email.lower().strip():
      return s['first'] + ' ' + s['last']
  return ''

def studentGrade(students, email):
  for s in students:
    if s['email'].lower().strip() == email.lower().strip():
      return str(s['current_grade'])
  return '0'

def getRosterClassObj(classes, roster):
  name = roster[0]
  instructor = roster[1]
  max_enrollment = roster[2]
  daypart = sorted(roster[3].split('/'))
  location = sorted(roster[4].split('/'))
  for c in classes:
    if ('instructor' in c):
      if (c['name'] == name and
          c['instructor'] == instructor and
          str(c['max_enrollment']) == max_enrollment and 
          sorted([s['daypart'] for s in c['schedule']]) == daypart and
          sorted([s['location'] for s in c['schedule']]) == location):
        return c
    else:
      if (c['name'] == name and
          str(c['max_enrollment']) == max_enrollment and 
          sorted([s['daypart'] for s in c['schedule']]) == daypart and
          sorted([s['location'] for s in c['schedule']]) == location):
        return c
  return {}

def getRosterEmails(students, roster):
  name = roster[5]
  grade = roster[6]
  for s in students:
    if (s['first'] in name and
        s['last'] in name and
        str(s['current_grade']) == grade):
      return s['email']
  return ''

class Rosters(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/rosters?%s" % urllib.urlencode(
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
    rosters = self.request.get("rosters")
    if not rosters:
      logging.fatal("no rosters")

    classes = models.Classes.FetchJson(institution, session)
    students = models.Students.FetchJson(institution, session)
    rosters = csv.reader(StringIO.StringIO(rosters))
    roster_class = {}
    for roster in rosters:
      if roster == []:
        continue
      if roster[0] != '':
        if roster_class != {}:
          models.ClassRoster.Store(institution, session, roster_class, student_emails)
        student_emails = ''
        roster_class = getRosterClassObj(classes, roster)
        student_emails += getRosterEmails(students, roster) + ', '
      else:
        student_emails += getRosterEmails(students, roster) + ', '
    models.ClassRoster.Store(institution, session, roster_class, student_emails)
    
    self.RedirectToSelf(institution, session, "saved rosters")

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
    rosters = ''
    classes = models.Classes.FetchJson(institution, session)
    students = models.Students.FetchJson(institution, session)
    classes = sorted(classes, key=lambda c: c['name'])
    for c in classes:
      class_roster = models.ClassRoster.FetchEntity(institution, session, c['id'])
      if ('None' not in class_roster['class_name'] and
          'Core' not in class_roster['class_name']):
        rosters += '"' + class_roster['class_name'] + '",'
        if 'instructor' in class_roster:
          rosters += '"' + class_roster['instructor'] + '",'
        else:
          rosters += '"",'
        rosters += '"' + str(class_roster['max_enrollment']) + '",'
        rosters += '"' + '/'.join(s['daypart'] for s in class_roster['schedule']) + '",'
        rosters += '"' + '/'.join(s['location'] for s in class_roster['schedule']) + '"'

        roster_students = [(studentFullName(students, s),
                            studentGrade(students, s)) for s in class_roster['emails']]
        roster_students = sorted(roster_students)
        if (len(roster_students) > 0):
          rosters += ',"' + roster_students[0][0] + '"'
          rosters += ',"' + roster_students[0][1] + '"\n'
        else:
          rosters += '\n'
        for s in roster_students[1:]:
          rosters += '"","","","","","' + s[0] + '",'
          rosters += '"' + s[1] + '"\n'

    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'rosters': rosters,
      'self': self.request.uri,
    }
    template = JINJA_ENVIRONMENT.get_template('rosters.html')
    self.response.write(template.render(template_values))
