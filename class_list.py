import os
import urllib
import jinja2
import webapp2
import logging

import models
import authorizer
import logic

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
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

class ClassList(webapp2.RequestHandler):
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

    classes = models.Classes.FetchJson(institution, session)
    dayparts = models.Dayparts.FetchJson(institution, session)
    dp_dict = {} # used for ordering by col then row
    for dp in dayparts:
      dp_dict[dp['name']] = str(dp['col'])+str(dp['row'])
    for c in classes:
      r = models.ClassRoster.FetchEntity(institution, session, c['id'])
      c['num_enrolled'] = len(r['emails'])
      w = models.ClassWaitlist.FetchEntity(institution, session, c['id'])
      c['num_waitlist'] = len(w['emails'])
      c['dayorder'] = dp_dict[c['schedule'][0]['daypart']]
    if classes:
      classes.sort(key=listOrder)
    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'classes': classes,
    }
    template = JINJA_ENVIRONMENT.get_template('class_list.html')
    self.response.write(template.render(template_values))
