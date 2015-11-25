import os
import urllib
import jinja2
import webapp2
import logging
import yaml
import itertools
import random

import models
import authorizer
import logic

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class ClassRoster(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, class_id):
    self.redirect("/class_list?%s" % urllib.urlencode(
        {'message': message,
         'institution': institution,
         'session': session,
         'class_id': class_id}))

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
    class_id = self.request.get("class_id")
    if not session:
      logging.fatal("no class id")

    message = self.request.get('message')
    session_query = urllib.urlencode({'institution': institution,
                                      'session': session})

    class_roster = models.ClassRoster.FetchEntity(institution, session, class_id)
    students = models.Students.fetch(institution, session)
    template_values = {
      'logout_url': auth.GetLogoutUrl(self),
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'class_roster': class_roster,
      'students': students
    }
    template = JINJA_ENVIRONMENT.get_template('class_roster.html')
    self.response.write(template.render(template_values))
