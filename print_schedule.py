import os
import urllib
import jinja2
import webapp2
import logging
import yaml

import models
import authorizer

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class PrintSchedule(webapp2.RequestHandler):
  def SortByName(self, classes):
    return sorted(classes, key=lambda e: e['name'])

  def CoreClasses(self, classes):
    return [c for c in classes if 'Core' in c['name']]

  def get(self):
    auth = authorizer.Authorizer(self)
    if not auth.HasStudentAccess():
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
    email = auth.student_email
    dayparts = models.Dayparts.FetchJson(institution, session)
    if not dayparts:
      dayparts = []
    schedule = models.Schedule.Fetch(institution, session, email)
    schedule = schedule.split(",")
    if schedule and schedule[0] == "":
      schedule = schedule[1:]
    classes = models.Classes.FetchJson(institution, session)
    try:
      _ = [c for c in classes]
    except TypeError:
      classes = []
    schedule_by_daypart = {}
    dayparts_ordered = []

    max_row = max([daypart['row'] for daypart in dayparts])
    max_col = max([daypart['col'] for daypart in dayparts])
      
    # order the dayparts by row and col specified in yaml
    for row in range(max_row):
      dayparts_ordered.append([])
      for col in range(max_col):
        found_daypart = False
        for dp in dayparts:
          if dp['row'] == row+1 and dp['col'] == col+1:
            dayparts_ordered[row].append(dp['name'])
            found_daypart = True
        if found_daypart == False:
          dayparts_ordered[row].append('')

    for daypart in dayparts:
      schedule_by_daypart[daypart['name']] = []
    admin_flag = auth.CanAdministerInstitutionFromUrl()
    for c in classes:
      if str(c['id']) in schedule:
        for daypart in [s['daypart'] for s in c['schedule']]:
          if daypart in schedule_by_daypart:
            schedule_by_daypart[daypart] = c

    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'student': auth.student_entity,
      'dayparts': dayparts,
      'schedule_by_daypart': schedule_by_daypart,
      'dayparts_ordered': dayparts_ordered,
    }
    template = JINJA_ENVIRONMENT.get_template('print_schedule.html')
    self.response.write(template.render(template_values))
  