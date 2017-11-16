import os
import urllib
import jinja2
import webapp2
import logging
import json
import datetime

import models
import authorizer
import logic

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(os.path.dirname(__file__))),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

# Implement the abstract base class 'tzinfo' to get Pacific Time
# which handles daylight savings.
class PT(datetime.tzinfo):
  def utcoffset(self, dt):
    return datetime.timedelta(hours=-8) + self.dst(dt)
  def dst(self, dt):
    # PDT starts the 2nd Sunday of March
    # and ends the 1st Sunday of November.
    d = datetime.datetime(dt.year, 3, 1)
    self.dston = d + datetime.timedelta(days = 14-d.weekday()-1)
    d = datetime.datetime(dt.year, 11, 1)
    self.dstoff = d + datetime.timedelta(days = 7-d.weekday()-1)
    if self.dston <= dt.replace(tzinfo=None) < self.dstoff:
      return datetime.timedelta(hours=1)
    return datetime.timedelta(0)
  def tzname(self, dt):
    return "Pacific Time"

def convertDayToStr(d):
  return {
    0: 'Mon',
    1: 'Tue',
    2: 'Wed',
    3: 'Thur',
    4: 'Fri',
    5: 'Sat',
    6: 'Sun',
  }[d]

def alphaOrder(c):
  if 'instructor' in c:
    return (c['name'],
            c['instructor'])
  else:
    return (c['name'])

def buildAttendance(institution, session, c, students):
  c['daypart'] = "/".join([str(dp['daypart'])
                           for dp in c['schedule']])
  c['location'] = "/".join([str(dp['location'])
                            for dp in c['schedule']])
  c['attendance'] = models.Attendance.FetchJson(institution,
                                                session,
                                                str(c['id']))
  if c['attendance']:
    pt = PT()
    today = datetime.datetime.now(pt).strftime("%a %b %d %Y")
    student_list = [s for email in c['attendance'][today]['absent']
                    for s in students if s['email'] == email]
    student_list.sort(key=(lambda(s): s['last']))
    c['absent'] = student_list

class AttendanceToday(webapp2.RequestHandler):
  def get(self):
    auth = authorizer.Authorizer(self)
    if not auth.HasTeacherAccess():
      auth.Redirect()
      return

    institution = self.request.get("institution")
    if not institution:
      logging.fatal("no institution")
    session = self.request.get("session")
    if not session:
      logging.fatal("no session")
    session_query = urllib.urlencode({'institution': institution,
                                      'session': session})

    todays_classes = []
    classes = models.Classes.FetchJson(institution, session)
    if not classes:
      classes = []
    pt = PT()
    searchday = convertDayToStr(datetime.datetime.now(pt).weekday())
    for c in classes:
      if 'Core' not in c['name']: # Shouldn't test for this here, but ...
        for s in c['schedule']:
          if searchday in s['daypart']:
            todays_classes.append(c)
    todays_classes.sort(key=alphaOrder)

    students = models.Students.FetchJson(institution, session)
    if not students:
      students = []
    for s in students:
      s['email'] = s['email'].lower()

    for c in todays_classes:
      buildAttendance(institution, session, c, students)

    template_values = {
      'institution' : institution,
      'session' : session,
      'session_query': session_query,
      'teacher': auth.teacher_entity,
      'todays_classes': json.dumps(todays_classes),
    }
    template = JINJA_ENVIRONMENT.get_template('teacher/attendance_today.html')
    self.response.write(template.render(template_values))