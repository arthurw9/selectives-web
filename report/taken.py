import os
import urllib
import jinja2
import webapp2
import logging

import models
import authorizer

'''
This page and the Not Taken page are used for generating
student groups. Listed below are different types of Student Groups
and how they are created.

Manually generated group - This group is usually chosen during the
pre-signup process. Instructors provide the selective team with
a list of pre-qualified students. This group type is not generated
from this page. Examples: Yearbook, French, Shakespeare To Go.

Taken 'XYZ' - Students who have previously taken class XYZ. From this
page, you can generate a student list from a specified class during a
specified session. You may need to combine lists from multiple
sessions as some students may have taken the class in a previous
semester or year. Examples: students who have taken Boxing qualify
for Advanced Boxing, Woodworking qualify for Advanced Woodworking.

Not Taken 'XYZ' - Students who have not yet taken class XYZ. To
generate this list, first create the list of students who HAVE taken
the class. (Remember, you may need to combine lists from multiple
sessions.) Then copy and paste the combined list into the Not Taken
page which will generate the inverse of the Taken list using students
from the current session. Examples: no repeat classes such as Boxing,
Woodworking, Cooking Block A, Cooking Block B.

Students from a particular grade or homeroom. Example: DowlingScience
is open only to students not from Rm 29. Use grade and homeroom instead
of Student Groups for this type of filter.

Auto-generated groups of lottery winners. These are generated from
the lottery page, not here.
'''
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(os.path.dirname(__file__))),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

def listOrder(c):
  if 'instructor' in c:
    return (c['name'],
            c['dayorder'],
            c['instructor'])
  else:
    return (c['name'],
            c['dayorder'])

class Taken(webapp2.RequestHandler):
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
    selected_class = self.request.get("class-dd")
    session_list = models.Session.FetchAllSessions(institution)
    class_list = []
    if selected_session:
      dayparts = models.Dayparts.FetchJson(institution, selected_session)
      dp_dict = {} # used for ordering by col then row
      for dp in dayparts:
        dp_dict[dp['name']] = str(dp['col'])+str(dp['row'])
      class_list = models.Classes.FetchJson(institution, selected_session)
      for c in class_list:
        c['dayorder'] = dp_dict[c['schedule'][0]['daypart']]
      if class_list: # Unfortunately, models returns '' if none.
        class_list.sort(key=listOrder)
    
    taken = []
    if selected_session and selected_class:
      taken = models.ClassRoster.FetchEntity(institution, selected_session, selected_class)

    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'selected_session': selected_session,
      'selected_class': selected_class,
      'session_list': session_list,
      'class_list': class_list,
      'taken': taken,
    }
    template = JINJA_ENVIRONMENT.get_template('report/taken.html')
    self.response.write(template.render(template_values))