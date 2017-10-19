import os
import urllib
import jinja2
import webapp2
import logging
import json

import models
import authorizer
import logic

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(os.path.dirname(__file__))),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

dayOrder = ['Mon A', 'Mon B', 'Tues A', 'Tues B',
            'Thurs A', 'Thurs B', 'Fri A', 'Fri B']

def listOrder(c):
  if 'instructor' in c:
    return (dayOrder.index(c['schedule'][0]['daypart']),
            c['name'],
            c['instructor'])
  else:
    return (dayOrder.index(c['schedule'][0]['daypart']),
            c['name'])

class MyAttendance(webapp2.RequestHandler):
  def get(self):
    auth = authorizer.Authorizer(self)
    if not auth.HasTeacherAccess():
      auth.Redirect()
      return

    user_type = 'None'
    if auth.HasTeacherAccess():
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
    email = auth.teacher_email

    classes = models.Classes.FetchJson(institution, session)
    if classes:
      classes.sort(key=listOrder)
    my_classes = []
    for c in classes:
      if 'owners' in c:
        for owner in c['owners']:
          if owner == auth.teacher_entity['email']:
            my_classes.append(c)
  
    rosters = {}
    for c in classes:
      rosters[c['id']] = models.ClassRoster.FetchEntity(institution, session, c['id'])
      c['num_locations'] = len(set(s['location'] for s in c['schedule']))
    students = models.Students.FetchJson(institution, session)
    for s in students:
      s['email'] = s['email'].lower()
    if students:
      students.sort(key=lambda(s): s['last'])
    template_values = {
      'user_type' : user_type,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'classes': my_classes,
      'rosters': rosters,
      'students': students,
    }
    template = JINJA_ENVIRONMENT.get_template('report/attendance_list.html')
    self.response.write(template.render(template_values))
    