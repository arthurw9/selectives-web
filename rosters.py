import os
import urllib
import jinja2
import webapp2
import logging
import csv
import StringIO

import yayv
import schemas
import error_check_logic
import models
import authorizer

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

def getStudentInfo(student_dict, email):
  if email in student_dict:
    s = student_dict[email]
    if 'edtechid' in s:
      return [s['first'],
              s['last'],
              str(s['current_grade']),
              str(s['current_homeroom']),
              str(s['edtechid'])]
    else:
      return [s['first'],
              s['last'],
              str(s['current_grade']),
              str(s['current_homeroom'])]
  else:
    logging.error('getStudentInfo: ' + email + ' not found in dictionary')
    return ''

def getClassObj(class_dict, line):
  if len(line) < 1:
    return {}
  id = line[0]
  if id in class_dict:
    return class_dict[id]
  else:
    return {}

def getStudentEmail(student_dict, line):
  if len(line) < 10:
    return ''
  first = line[6]
  last = line[7]
  grade = line[8]
  homerm = line[9]

  key = first + last + grade + homerm
  if key in student_dict:
    return student_dict[key]
  else:
    return ''

class Rosters(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/rosters?%s" % urllib.urlencode(
        {'message': message, 
         'institution': institution,
         'session': session}))

  def post(self):
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
    rosters = self.request.get("rosters")
    if not rosters:
      logging.fatal("no rosters")

    class_put_dict = {} # {79:{'name':'3D Printing', etc.}}
    student_put_dict = {} # {'firstlast623': 'first.last19@mydiscoverk8.org'}
    student_put_sched = {} # {'first.last19@mydiscoveryk8.org': [5,6,29,79,10]}

    classes = models.Classes.FetchJson(institution, session)
    for c in classes:
      key = str(c['id'])
      class_put_dict[key] = c

    students = models.Students.FetchJson(institution, session)
    for s in students:
      key = s['first'] +\
            s['last'] +\
            str(s['current_grade']) +\
            str(s['current_homeroom'])
      student_put_dict[key] = s['email'].strip().lower()
      student_put_sched[s['email'].strip().lower()] = []

    # Replace class rosters and build student_put_sched
    rosters = csv.reader(StringIO.StringIO(rosters))
    curr_class_obj = {}
    student_emails = ''
    for line in rosters:
      # If line contains only student info
      if line != [] and line[0] == '':
        curr_email = getStudentEmail(student_put_dict, line).strip().lower()
        if curr_email in student_put_sched:
          student_put_sched[curr_email].append(curr_class_obj['id'])
          student_emails += curr_email + ','
        else:
          logging.error("Invalid email: " + curr_email +\
                        "at line: " + str(line))
      # Else, the line contains class data i.e. start of a new class
      # Or it's the last empty line []
      else:
        # If currently processing a roster, store it.
        if curr_class_obj != {}:
          models.ClassRoster.Store(institution, session,
                                   curr_class_obj,
                                   student_emails)
        # Get new class data and start building new email list
        student_emails = ''
        curr_class_obj = getClassObj(class_put_dict, line)
        if curr_class_obj == {} and line != []:
          logging.error("curr_class_obj: " + str(curr_class_obj) +\
                        " at line: " + str(line))
        curr_email = getStudentEmail(student_put_dict, line).strip().lower()
        if curr_email in student_put_sched:
          student_put_sched[curr_email].append(curr_class_obj['id'])
          student_emails += curr_email + ','
        elif line != []:
          logging.error("email: " + curr_email +\
                        "at line: " + str(line))

    # Replace student schedules using dictionary built above
    for email_key in student_put_sched:
      models.Schedule.Store(institution, session,
                            email_key,
                            ','.join(str(cid) for cid in student_put_sched[email_key]))

    self.RedirectToSelf(institution, session, "saved rosters")

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

    student_get_dict = {} # {'John.Smith19@mydiscoveryk8.org': {'first':'John', 'last':'Smith', etc.}}
    for s in students:
      student_get_dict[s['email'].strip().lower()] = s

    for c in classes:
      class_roster = models.ClassRoster.FetchEntity(institution, session,
                                                    c['id'])
      if (len(class_roster['emails']) <= 0):
        continue
      rosters += '"' + str(c['id']) + '",'
      rosters += '"' + c['name'] + '",'
      if 'instructor' in c and c['instructor'] != None:
        rosters += '"' + c['instructor'] + '",'
      else:
        rosters += '"",'
      rosters += '"' + str(c['max_enrollment']) + '",'
      rosters += '"' + '/'.join(s['daypart'] for s in c['schedule']) + '",'
      rosters += '"' + '/'.join(str(s['location']) for s in c['schedule']) + '"'

      roster_students = [getStudentInfo(student_get_dict, s) for s in class_roster['emails']]
      roster_students = sorted(roster_students)
      if (len(roster_students) > 0):
        for student_data_field in roster_students[0]:
          rosters += ',"' + student_data_field + '"'
      rosters += '\n'
      for s in roster_students[1:]:
        if s:
          rosters += '"","","","","","","' + s[0] + '"'
          for student_data_field in s[1:]:
            rosters += ',"' + student_data_field + '"'
          rosters += '\n'
        else:
          logging.error("Student in roster_students is empty string!")

    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'rosters': rosters,
      'self': self.request.uri,
    }
    template = JINJA_ENVIRONMENT.get_template('rosters.html')
    self.response.write(template.render(template_values))
