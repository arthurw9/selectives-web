import os
import urllib
import jinja2
import webapp2
import logging
import datetime

import models
import authorizer

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

class MyStudents(webapp2.RequestHandler):
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
    classes_by_id = {}
    classes = models.Classes.FetchJson(institution, session)
    for c in classes:
      classes_by_id[c['id']] = c
    students = models.Students.FetchJson(institution, session)
    last_modified_overall = datetime.datetime(2000,1,1)
    last_modified_overall_str = ''
    hmrm = 'None'
    if 'current_homeroom' in auth.teacher_entity:
      hmrm = auth.teacher_entity['current_homeroom']
    my_students = []
    for s in students:
      if hmrm == 'None' or s['current_homeroom'] == hmrm:
        s['email'] = s['email'].lower()
        sched_obj = models.Schedule.FetchEntity(institution, session, s['email'])
        s['sched'] = sched_obj.class_ids
        s['last_modified'] = sched_obj.last_modified
        if sched_obj.last_modified:
          s['last_modified'] = str(sched_obj.last_modified.month) + '/' +\
                               str(sched_obj.last_modified.day) + '/' +\
                               str(sched_obj.last_modified.year)
          if sched_obj.last_modified > last_modified_overall:
            last_modified_overall = sched_obj.last_modified
            last_modified_overall_str = s['last_modified']
        if (s['sched']):
          s['sched'] = s['sched'].split(',')
          for cId in s['sched']:
            cId_class = classes_by_id[int(cId)]
            for dp in cId_class['schedule']:
              if dp['location'] == 'Homeroom':
                s[dp['daypart']] = 'Core'
              else:
                s[dp['daypart']] = dp['location'] + ', ' +        cId_class['name']
              s[dp['daypart']] = s[dp['daypart']][0:26]
        my_students.append(s)
    if my_students:
      my_students.sort(key=lambda(s): s['last'])
    template_values = {
      'user_type' : user_type,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'students': my_students,
      'last_modified': last_modified_overall_str,
    }
    template = JINJA_ENVIRONMENT.get_template('report/student_schedules.html')
    self.response.write(template.render(template_values))
    