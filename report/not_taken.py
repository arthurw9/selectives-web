import os
import urllib
import jinja2
import webapp2
import logging
import yaml
import re
from sets import Set
import operator

import models
import authorizer

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(os.path.dirname(__file__))),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

def removeTaken(taken, students):
  return [s for s in students if s['email'] not in taken]

# Strips off leading string "Taken" and possible underscore "_".
# For example, given either "Taken_Boxing" or "TakenBoxing", returns "Boxing"
def getClassNameId(taken):
  y = yaml.load(taken)
  if y and 'group_name' in y[0]:
    g_name = y[0]['group_name']
    if "_" in g_name:
      g_name = removePrefix(g_name, "taken_")
    else:
      g_name = removePrefix(g_name, "taken")
    return g_name
  else:
    return ''

# Removes prefix from str, case-insensitive
def removePrefix(str, prefix):
  if bool(re.match(prefix, str, re.I)):
    return str[len(prefix):]
  return str

# Get grade levels from student list so they aren't hardcoded in the html page.
def getGradeLevels(students):
  # Use Set to get unique grade levels
  grade_set = Set()
  for s in students:
    grade_set.add(s['current_grade'])
  # Because sets are not sorted, save into array to sort
  grade_levels = []
  for g in grade_set:
    grade_levels.append([g, "grade"+str(g)])
  grade_levels.sort(reverse=True) # highest grade first
  return grade_levels

class NotTaken(webapp2.RequestHandler):
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

    selected_session = self.request.get("session-dd")
    if not selected_session:
      selected_session = session

    session_list = models.Session.FetchAllSessions(institution)

    taken = self.request.get("taken")
    students = models.Students.FetchJson(institution, selected_session)
    not_taken = removeTaken(taken, students)
    class_name_id = getClassNameId(taken)

    grade_levels = getGradeLevels(students)

    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'selected_session': selected_session,
      'session_list': session_list,
      'taken': taken,
      'not_taken': not_taken,
      'class_name_id': class_name_id,
      'grade_levels': grade_levels,
    }
    template = JINJA_ENVIRONMENT.get_template('report/not_taken.html')
    self.response.write(template.render(template_values))