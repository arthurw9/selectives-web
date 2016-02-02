import os
import urllib
import jinja2
import webapp2
import logging
import yaml

import models
import authorizer

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class CatalogPrint(webapp2.RequestHandler):
  def SortByName(self, classes):
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
    message = self.request.get('message')
    session_query = urllib.urlencode({'institution': institution,
                                      'session': session})
    classes = models.Classes.FetchJson(institution, session)
    classes = self.SortByName(classes)
    core = self.CoreClasses(classes)
    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'classes': classes,
      'core': core,
    }
    template = JINJA_ENVIRONMENT.get_template('catalog_print.html')
    self.response.write(template.render(template_values))
  