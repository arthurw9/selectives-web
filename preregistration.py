import os
import urllib
import jinja2
import webapp2
import logging
import yaml

import models
import authorizer
import schemas

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Preregistration(webapp2.RequestHandler):
  def SortByName(self, classes):
    if not classes:
      return ''
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
    session_query = urllib.urlencode({'institution': institution,
                                      'session': session})
    classes = models.Classes.FetchJson(institution, session)
    classes = self.SortByName(classes)
    core = self.CoreClasses(classes)
    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'session_query': session_query,
      'student': auth.student_entity,
      'classes': classes,
      'core': core,
    }
    template = JINJA_ENVIRONMENT.get_template('preregistration.html')
    self.response.write(template.render(template_values))
  