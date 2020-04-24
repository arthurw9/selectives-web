import os
import urllib
import jinja2
import webapp2

import models
import authorizer

# I created a report subdirectory for various reports needed in the scheduling process.
# Since we are inside the report folder, I need to call
# os.path.dirname(os.path.dirname(...)) to go up to the parent directory.
# This is necessary because Jinja doesn't allow .. notation in extends
# in other words {% extends '../menu.html' %} is not possible.
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(os.path.dirname(__file__))),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

def listOrder(c):
  if 'instructor' in c:
    return (c['name'],
            c['dayorder'],
            c['instructor'])
  else:
    return (c['name'],
            c['dayorder'])

class AttendanceList(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/report/attendance_list?%s" % urllib.urlencode(
        {'message': message,
         'institution': institution,
         'session': session}))

  def get(self):
    auth = authorizer.Authorizer(self)
    if not (auth.CanAdministerInstitutionFromUrl() or
            auth.HasTeacherAccess()):
      auth.Redirect()
      return

    user_type = 'None'
    if auth.CanAdministerInstitutionFromUrl():
      user_type = 'Admin'
    elif auth.HasTeacherAccess():
      user_type = 'Teacher'

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
    dayparts = models.Dayparts.FetchJson(institution, session)
    dp_dict = {} # used for ordering by col then row
    for dp in dayparts:
      dp_dict[dp['name']] = str(dp['col'])+str(dp['row'])
    rosters = {}
    for c in classes:
      rosters[c['id']] = models.ClassRoster.FetchEntity(institution, session, c['id'])
      c['num_locations'] = len(set(s['location'] for s in c['schedule']))
      c['dayorder'] = dp_dict[c['schedule'][0]['daypart']]
    if classes:
      classes.sort(key=listOrder)
    students = models.Students.FetchJson(institution, session)
    for s in students:
      s['email'] = s['email'].lower()
    if students:
      students.sort(key=lambda(s): s['last'])
    template_values = {
      'user_email' : auth.email,
      'user_type' : user_type,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'classes': classes,
      'rosters': rosters,
      'students': students,
    }
    template = JINJA_ENVIRONMENT.get_template('report/attendance_list.html')
    self.response.write(template.render(template_values))
