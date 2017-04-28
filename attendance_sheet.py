import os
import urllib
import jinja2
import webapp2
import logging

import models
import authorizer

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

NUM_COLS = 19

def getOriginalClassDetails(classes, class_id):
  for c in classes:
    if (str(c['id']) == class_id):
      c['num_locations'] = len(set(s['location'] for s in c['schedule']))
      return c
  return None

def getStudentDetails(students, roster_emails):
  studentList = []
  for s in students:
    for r in roster_emails:
      if s['email'].strip().lower() == r.strip().lower():
        studentList.append(s)
        break
  return studentList

class AttendanceSheet(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, class_id, message):
    self.redirect("/attendance_sheet?%s" % urllib.urlencode(
        {'message': message,
         'institution': institution,
         'session': session,
         'class_id': class_id}))

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
    students = models.Students.FetchJson(institution, session)
    students = getStudentDetails(students, class_roster['emails'])
    students.sort(key=lambda s: s['first']+s['last'])
    classes = models.Classes.FetchJson(institution, session)
    class_details = getOriginalClassDetails(classes, class_id)
    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'class_roster': class_roster,
      'students': students,
      'class_details': class_details,
      'num_cols': NUM_COLS,
    }
    template = JINJA_ENVIRONMENT.get_template('attendance_sheet.html')
    self.response.write(template.render(template_values))
