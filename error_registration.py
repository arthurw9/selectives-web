import os
import urllib
import jinja2
import webapp2
import logging

import models
import authorizer

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

ALL_GRADES = 100

# Takes a schedule object
#   {'Mon A': {'name': 'PE',
#              'fitness': True,},
#    . . .}
# Returns 0 if no error, integer error value otherwise
def checkPE(schedule_by_dp):
  num_PE = num_Dance = num_fitness = num_PE_MT = num_PE_TF = 0
  for dp_key, dp_obj in schedule_by_dp.iteritems():
    if (dp_obj['name'] == 'PE'):
      num_PE += 1
      if (dp_key.startswith('Mon') or
          dp_key.startswith('Tues')):
        num_PE_MT += 1
      if (dp_key.startswith('Thurs') or
          dp_key.startswith('Fri')):
        num_PE_TF += 1
    if (dp_obj['name'] == 'Dance'):
      num_Dance += 1
    if (dp_obj['fitness'] == True):
      num_fitness += 1
  if (num_PE < 1 and num_Dance < 2):
    return 1 # Must have at least one actual PE or Dance
  if num_PE > 2:
    return 2 # Cannot take more than two actual PE classes
  if num_fitness < 2:
    return 3 # Must have at least two fitness classes in all
  if num_fitness > 3:
    return 4 # Cannot take more than three fitness classes in all
  if num_PE_MT > 1 or num_PE_TF > 1:
    return 5 # PE cannot be on same half of the week
  return 0 # No errors found

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
    grade_level = self.request.get("grade_level")
    if not grade_level:
      grade_level = ALL_GRADES # default
    grade_level = int(grade_level)
    message = self.request.get('message')
    session_query = urllib.urlencode({'institution': institution,
                                      'session': session})

    err_list = [] # list of tuples where
                  #   first element is the error message
                  #   second element is the student object
                  #   third element is the student schedule object by daypart

    classes = models.Classes.FetchJson(institution, session)
    classes_by_id = {}
    for c in classes:
      classes_by_id[c['id']] = c

    students = models.Students.FetchJson(institution, session)
    for s in students:
      if (grade_level != ALL_GRADES) and (s['current_grade'] != grade_level):
        continue
      sched_obj = models.Schedule.FetchEntity(institution, session,
                                              s['email'].lower())
      if not(sched_obj and sched_obj.class_ids):
        err_list.append(('Missing schedule', s, {}))
        continue
      s['sched'] = sched_obj.class_ids.split(',')
      schedule_by_dp = {}
      for cId in s['sched']:
        cId_class = classes_by_id[int(cId)]
        for dp in cId_class['schedule']:
          schedule_by_dp[dp['daypart']] = {
            'name': cId_class['name'],
            'location': dp['location'],
            'fitness': cId_class.get('fitness', False)}
      if (len(schedule_by_dp) != 8):
        err_list.append(('Incomplete schedule', s, schedule_by_dp))
        continue
      err_val = checkPE(schedule_by_dp)
      if err_val == 0:
        continue
      if err_val == 1:
        err_list.append(('Missing PE or Dance', s, schedule_by_dp))
      if err_val == 2:
        err_list.append(('Too many PEs, maximum is two', s, schedule_by_dp))
      if err_val == 3:
        err_list.append(('Not enough PE or alternatives, minimum is two', s, schedule_by_dp))
      if err_val == 4:
        err_list.append(('Too many PE or alternatives, maximum is three', s, schedule_by_dp))
      if err_val == 5:
        err_list.append(('Only one PE allowed Mon-Tues, Thurs-Fri', s, schedule_by_dp))

    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'err_list': err_list,
      'session_query': session_query,
    }
    template = JINJA_ENVIRONMENT.get_template('error_registration.html')
    self.response.write(template.render(template_values))
