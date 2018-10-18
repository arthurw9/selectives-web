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

def orderScheduleByDP(sched_obj, classes_by_id):
  schedule_by_dp = {}
  sched_list = sched_obj.class_ids.split(',')
  for cId in sched_list:
    c = classes_by_id[int(cId)]
    for dp in c['schedule']:
      schedule_by_dp[dp['daypart']] = {
          'name': c['name'],
          'location': dp['location'],
          'fitness': c.get('fitness', False)}
  return schedule_by_dp

def getErrorMsgs(schedule_by_dp, len_dayparts, institution, session):
  err_msgs = []
  if (len(schedule_by_dp) != len_dayparts):
    err_msgs.append("Incomplete schedule")
  err_msgs.extend(getFitnessErrorMsgs(schedule_by_dp))
  return err_msgs

# Takes a schedule object
#   {'Mon A': {'name': 'PE',
#              'fitness': True,},
#    . . .}
# Returns list of error messages, [] if no error
def getFitnessErrorMsgs(schedule_by_dp):
  num_PE = num_Dance = num_fitness = num_PE_MT = num_PE_TF = 0
  err_msgs = []
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
    err_msgs.append("At least one PE or Dance required.")
  if num_PE > 2:
    err_msgs.append("Too many PE's, maximum is two.")
  if num_fitness < 2:
    err_msgs.append("At least two PE or PE alternatives required.")
  if num_fitness > 3:
    err_msgs.append("Too many PE or PE alternatives, maximum is three.")
  if num_PE_MT > 1 or num_PE_TF > 1:
    err_msgs.append("Not allowed to have two PE's on Mon/Tues or Thurs/Fri.")
  return err_msgs

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

    err_list = [] # list of tuples where
                  #   first element contains a list of error messages
                  #   second element is the student object
                  #   third element is the student schedule object by daypart

    grade_level = self.request.get("grade_level")
    if grade_level:
      grade_level = int(grade_level)
      len_dayparts = len(models.Dayparts.FetchJson(institution, session))

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
          err_list.append((['Missing schedule'], s, {}))
          continue # Entire schedule is missing,
                   # don't bother checking for further errors
        schedule_by_dp = orderScheduleByDP(sched_obj, classes_by_id)
        err_msgs = getErrorMsgs(schedule_by_dp, len_dayparts, institution, session)
        if err_msgs != []:
          err_list.append((err_msgs, s, schedule_by_dp))
    # else no button was clicked, don't do anything

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
