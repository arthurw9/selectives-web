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

def buildRoster(c, roster, attendance, students):
  r = {}
  r['name'] = c['name']
  if 'instructor' in c:
    r['instructor'] = c['instructor']
  r['daypart'] = "/".join([str(dp['daypart'])
                           for dp in c['schedule']])
  r['location'] = "/".join([str(dp['location'])
                            for dp in c['schedule']])
  r['emails'] = roster['emails']
  student_list = [students[email] for email in roster['emails']]
  student_list.sort(key=(lambda(s): s['last']))
  r['students'] = student_list
  if attendance:
    r['submitted_by'] = attendance['submitted_by']
    # for students not found (withdrawn from school), set last = '_None'
    r['present'] = [students[email] if email in students\
                    else {'email': email, 'last': '_None'}\
                    for email in attendance['present'] ]
    r['present'].sort(key=(lambda(s): s['last']))
    r['absent'] = [students[email] if email in students\
                   else {'email': email, 'last': '_None'}\
                   for email in attendance['absent']]
    r['absent'].sort(key=(lambda(s): s['last']))
    r['submitted_date'] = attendance['submitted_date']
    if 'note' in attendance:
      r['note'] = attendance['note']
    else:
      r['note'] = ''
  return r

def alphaOrder(c):
  return (c['name'],
          c['dayorder'],
          c['instructor'])

def buildClasses(auth, dayparts, classes, my_classes, other_classes):
  dp_dict = {}
  for dp in dayparts:
    dp_dict[dp['name']] = str(dp['col'])+str(dp['row'])
  for c in classes:
    c['dayorder'] = dp_dict[c['schedule'][0]['daypart']]
    c['daypart'] = "/".join([str(dp['daypart'])
                             for dp in c['schedule']])
    if 'instructor' not in c:
      c['instructor'] = 'none'
    hasOwner = False
    if 'owners' in c:
      for owner in c['owners']:
        if owner == auth.teacher_entity['email']:
          hasOwner = True
          my_classes.append(c)
    if not hasOwner:
      other_classes.append(c)
  my_classes.sort(key=alphaOrder)
  other_classes.sort(key=alphaOrder)

class TakeAttendance(webapp2.RequestHandler):
  def RedirectToSelf(self, institution, session, selected_cid, selected_date):
    self.redirect("/teacher/take_attendance?%s" % urllib.urlencode(
        {'institution': institution,
         'session': session,
         'selected_cid': selected_cid,
         'selected_date': selected_date}))

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
    submitted_date = self.request.get("submitted_date")
    if not submitted_date:
      logging.fatal("no date")
    c_id = self.request.get("c_id")
    if not c_id:
      logging.fatal("no class id")
    present_kids = self.request.get("present_kids")
    absent_kids = self.request.get("absent_kids")
    if present_kids:
      present_kids = [e for e in present_kids.split(',')]
    else:
      present_kids = []
    if absent_kids:
      absent_kids = [e for e in absent_kids.split(',')]
    else:
      absent_kids = []
    note = self.request.get("note")
    teachers = models.Teachers.FetchJson(institution, session)
    teacher = logic.FindUser(auth.email, teachers)
    attendanceObj = {
      "present": present_kids,
      "absent": absent_kids,
      "submitted_by": " ".join([teacher['first'], teacher['last']]),
      "submitted_date": submitted_date,
      "note": note,
    }
    models.Attendance.store(institution, session, c_id, submitted_date, attendanceObj)
    self.RedirectToSelf(institution, session, c_id, submitted_date)

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
    selected_cid = self.request.get('selected_cid')
    logging.info("selected_cid: " + selected_cid)
    selected_date = self.request.get('selected_date')
    logging.info("selected_date: " + selected_date)
    session_query = urllib.urlencode({'institution': institution,
                                      'session': session,
                                      'current_cid': selected_cid})
    if not selected_cid:
      selected_cid = 0

    dayparts = models.Dayparts.FetchJson(institution, session)
    classes = models.Classes.FetchJson(institution, session)
    if not classes: classes = []
    my_classes = []
    other_classes = []
    buildClasses(auth, dayparts, classes, my_classes, other_classes)

    students = models.Students.FetchJson(institution, session)
    # create a dictionary of students to avoid multiple loops in buildRoster
    students_dict = {}
    if not students: students = []
    for s in students:
      s['email'] = s['email'].lower()
      students_dict[s['email']] = s
    #logging.info(students_dict)

    my_roster = {}
    if selected_cid != 0 and selected_date:
      selected_attendance = models.Attendance.FetchJson(institution, session,
                                                        selected_cid, selected_date)
      selected_class = next(c for c in classes if c['id'] == int(selected_cid))
      selected_roster = models.ClassRoster.FetchEntity(institution, session, selected_cid)
      if not selected_roster:
        selected_roster = {}
      my_roster = buildRoster(selected_class, selected_roster, selected_attendance,
                              students_dict)
      logging.info(my_roster)
    # my_classes and other_classes are lists of classes
    # my_roster is a dictionary:
    # {'name': 'Circuit Training',
    #  'instructor': 'name',
    #    ...,
    #  'emails': [list of student emails],
    #  'students': [list of student objects based on the emails]}
    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'current_cid': selected_cid,
      'current_date': selected_date,
      'session_query': session_query,
      'teacher': auth.teacher_entity,
      'my_classes': my_classes,
      'my_roster': json.dumps(my_roster),
      'other_classes': other_classes,
    }
    template = JINJA_ENVIRONMENT.get_template('teacher/take_attendance.html')
    self.response.write(template.render(template_values))
