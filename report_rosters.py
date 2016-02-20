import os
import urllib
import jinja2
import webapp2
import logging
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
  logging.info(email.lower().strip())
  for s in students:
    if s['email'].lower().strip() == email.lower().strip():
      return s['first'] + ' ' + s['last']
  return ''

def studentGrade(students, email):
  for s in students:
    if s['email'].lower().strip() == email.lower().strip():
      return str(s['current_grade'])
  return '0'

class ReportRosters(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/report_rosters?%s" % urllib.urlencode(
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
        if (len(class_roster['emails']) > 0):
          rosters += ',"' + studentFullName(students, class_roster['emails'][0]) + '"'
          rosters += ',"' + studentGrade(students, class_roster['emails'][0]) + '"\n'
        else:
          rosters += '\n'
        for s in class_roster['emails'][1:]:
          rosters += '"","","","","","' + studentFullName(students, s) + '",'
          rosters += '"' + studentGrade(students, s) + '"\n'

    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'rosters': rosters,
      'self': self.request.uri,
    }
    template = JINJA_ENVIRONMENT.get_template('report_rosters.html')
    self.response.write(template.render(template_values))
