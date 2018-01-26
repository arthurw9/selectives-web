import os
import urllib
import jinja2
import webapp2

import models
import authorizer

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

dayOrder = ['Mon A', 'Mon B', 'Tues A', 'Tues B',
            'Thurs A', 'Thurs B', 'Fri A', 'Fri B']

def listOrder(d):
  return dayOrder.index(d['daypart'])

class ErrorRegistration(webapp2.RequestHandler):
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

    registration_detail = 'Schedule Errors:\n\n'
    foundError = False
    num_students = 0
    classes_by_id = {}
    classes = models.Classes.FetchJson(institution, session)
    for c in classes:
      classes_by_id[c['id']] = c
    students = models.Students.FetchJson(institution, session)
    for s in students:
      s['email'] = s['email'].lower()
      sched_obj = models.Schedule.FetchEntity(institution, session, s['email'])
      if sched_obj and sched_obj.class_ids:
        dayparts = []
        s['sched'] = sched_obj.class_ids
        s['sched'] = s['sched'].split(',')
        for cId in s['sched']:
          cId_class = classes_by_id[int(cId)]
          for dp in cId_class['schedule']:
            dp_obj = {}
            dp_obj['daypart'] = dp['daypart']
            dp_obj['name'] = cId_class['name']
            dp_obj['location'] = dp['location']
            dayparts.append(dp_obj)
        if (len(dayparts) != 8):
          registration_detail += s['first'] + ' ' +\
                                 s['last'] + ' ' +\
                                 str(s['current_grade']) + ' ' +\
                                 str(s['current_homeroom']) + '\n'
          dayparts.sort(key=listOrder)
          for dp_obj in dayparts:
            registration_detail += dp_obj['daypart'] + ' ' +\
                                   dp_obj['name'] + ' ' +\
                                   dp_obj['location'] + '\n'
          registration_detail += '\n'
          foundError = True
      else:
        registration_detail += 'Missing schedule: ' +\
                                s['first'] + ' ' +\
                                s['last'] + ' ' +\
                                str(s['current_grade']) + ' ' +\
                                str(s['current_homeroom']) + '\n'
        foundError = True
      num_students += 1
    if (foundError == False):
      registration_detail += 'All schedules look good!\n'
      registration_detail += 'Total students processed: ' +\
                             str(num_students) + '\n'
    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'registration_detail': registration_detail,
      'session_query': session_query,
    }
    template = JINJA_ENVIRONMENT.get_template('error_registration.html')
    self.response.write(template.render(template_values))
