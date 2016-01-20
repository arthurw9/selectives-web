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
  def RedirectToSelf(self, institution, session):
    self.redirect("/preregistration?%s" % urllib.urlencode(
        {'institution': institution,
         'session': session}))

  def RedirectToPage(self, page, institution, session):
    self.redirect("/%s?%s" % (page, urllib.urlencode(
        {'institution': institution,
         'session': session})))

  def SortByName(self, classes):
    return sorted(classes, key=lambda e: e['name'])

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
    self.RedirectToSelf(institution, session)

  def get(self):
    auth = authorizer.Authorizer(self)
    if not (auth.CanAdministerInstitutionFromUrl() or
            auth.HasStudentAccess()):
      auth.Redirect()
      return

    student = ''
    if auth.HasStudentAccess():
      student = auth.student_entity
    
    institution = self.request.get("institution")
    if not institution:
      logging.fatal("no institution")
    session = self.request.get("session")
    if not session:
      logging.fatal("no session")
    session_query = urllib.urlencode({'institution': institution,
                                      'session': session})
    classes = models.Classes.Fetch(institution, session)
    classes = yaml.load(classes)
    classes = self.SortByName(classes)
    template_values = {
      'logout_url': auth.GetLogoutUrl(self),
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'session_query': session_query,
      'student': student,
      'classes': classes,
    }
    template = JINJA_ENVIRONMENT.get_template('preregistration.html')
    self.response.write(template.render(template_values))
  