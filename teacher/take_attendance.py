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

def daypartOrder(c):
  if 'instructor' in c:
    return (c['dayorder'],
            c['name'],
            c['instructor'])
  else:
    return (c['dayorder'],
            c['name'])

def alphaOrder(c):
  if 'instructor' in c:
    return (c['name'],
            c['dayorder'],
            c['instructor'])
  else:
    return (c['name'],
            c['dayorder'])

def buildRoster(institution, session, c, students):
  r = {}
  r['name'] = c['name']
  if 'instructor' in c:
    r['instructor'] = c['instructor']
  r['daypart'] = "/".join([str(dp['daypart'])
                           for dp in c['schedule']])
  r['location'] = "/".join([str(dp['location'])
                            for dp in c['schedule']])
  roster = models.ClassRoster.FetchEntity(institution, session, c['id'])
  if not roster:
    roster = {}
  r['emails'] = roster['emails']
  student_list = [s for email in roster['emails']
                  for s in students if s['email'] == email]
  student_list.sort(key=(lambda(s): s['last']))
  r['students'] = student_list
  return r

class TakeAttendance(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/teacher/take_attendance?%s" % urllib.urlencode(
        {'message': message,
         'institution': institution,
         'session': session}))

  def post(self):
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
    today = self.request.get("today")
    if not today:
      logging.fatal("no date")
    c_id = self.request.get("c_id")
    if not c_id:
      logging.fatal("no class id")
    present_kids = self.request.get("present_kids")
    absent_kids = self.request.get("absent_kids")
    present_kids = [e for e in present_kids.split(',')]
    absent_kids = [e for e in absent_kids.split(',')]
    all_kids = {
      "present": present_kids,
      "absent": absent_kids
    }
    #models.Attendance.store(institution, session,
    #                        today, c_id, all_kids)
    absences = models.Attendance.FetchJson(institution, session, c_id)
    absences[today] = all_kids
    logging.info(absences)
    models.Attendance.store(institution, session, c_id, absences)
    self.RedirectToSelf(institution, session, "saved attendance")

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
    message = self.request.get('message')
    session_query = urllib.urlencode({'institution': institution,
                                      'session': session})

    # TODO: How to save the current dropdown selection upon
    # screen refresh?
    classes = models.Classes.FetchJson(institution, session)
    dayparts = models.Dayparts.FetchJson(institution, session)
    dp_dict = {}
    for dp in dayparts:
      dp_dict[dp['name']] = str(dp['col'])+str(dp['row'])
    if not classes:
      classes = []
    my_classes = []
    other_classes = []
    for c in classes:
      c['dayorder'] = dp_dict[c['schedule'][0]['daypart']]
      hasOwner = False
      if 'owners' in c:
        for owner in c['owners']:
          if owner == auth.teacher_entity['email']:
            hasOwner = True
            my_classes.append(c)
      if not hasOwner:
        other_classes.append(c)
    my_classes.sort(key=daypartOrder)
    other_classes.sort(key=alphaOrder)

    students = models.Students.FetchJson(institution, session)
    if not students:
      students = []
    for s in students:
      s['email'] = s['email'].lower()

    # TODO: show previous absences if already took attendance today
    #absences = models.Attendance.FetchJson(institution, session,
    #                                       'Wed Nov 01 2017', '35')
    #logging.info(absences)

    my_rosters = {}
    for c in my_classes:
      my_rosters[c['id']] = buildRoster(institution, session,
                                        c, students)

    other_rosters = {}
    for c in other_classes:
      other_rosters[c['id']] = buildRoster(institution, session,
                                           c, students)
# my_classes and other_classes are lists of classes
# my_rosters and other_rosters are dictionaries:
# {cid1: {'name': 'Circuit Training',
#         'instructor': 'name',
#          ...,
#         'emails': [list of student emails],
#         'students': [list of student objects based on the emails]},
# {cid2: ...}}
    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'teacher': auth.teacher_entity,
      'my_classes': my_classes,
      'my_rosters': json.dumps(my_rosters),
      'other_classes': other_classes,
      'other_rosters': json.dumps(other_rosters),
    }
    template = JINJA_ENVIRONMENT.get_template('teacher/take_attendance.html')
    self.response.write(template.render(template_values))
