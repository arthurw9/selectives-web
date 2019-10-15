import os
import urllib
import jinja2
import webapp2
import logging

import models
import authorizer

# Since we are inside the report directory, but Jinja doesn't allow
# {% extends '../menu.html' %}, call os.path.dirname(os.path.dirname())
# to go up to the parent directory.
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(os.path.dirname(__file__))),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

dayOrder = ['Mon A', 'Mon B', 'Tues A', 'Tues B',
            'Thurs A', 'Thurs B', 'Fri A', 'Fri B']

def listOrder(c):
  if 'instructor' in c:
    return (c['name'],
            dayOrder.index(c['schedule'][0]['daypart']),
            c['instructor'])
  else:
    return (c['name'],
            dayOrder.index(c['schedule'][0]['daypart']))

def addStudentData(class_roster, students_by_email):
  class_roster['students'] = []
  for e in class_roster['emails']:
    class_roster['students'].append(students_by_email[e])

class SignupMain(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/report/signup_main?%s" % urllib.urlencode(
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

    classes = models.Classes.FetchJson(institution, session)
    if classes:
      classes.sort(key=listOrder)
    students = models.Students.FetchJson(institution, session)
    students_by_email = {}
    for s in students:
      s['email'] = s['email'].lower()
      students_by_email[s['email']] = s
    if students:
      students.sort(key=lambda(s): s['last'])
    class_rosters = {}
    for c in classes:
      class_roster = models.ClassRoster.FetchEntity(institution, session, c['id'])
      class_roster['emails'].sort()
      addStudentData(class_roster, students_by_email)
      class_rosters[c['id']] = class_roster
    logging.info(class_rosters)
    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'classes': classes,
      'class_rosters': class_rosters,
    }
    template = JINJA_ENVIRONMENT.get_template('report/signup_main.html')
    self.response.write(template.render(template_values))