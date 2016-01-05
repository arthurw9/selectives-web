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
import error_check_logic
import yayv
import schemas

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class ErrorCheck(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/error_check?%s" % urllib.urlencode(
        {'message': message, 
         'institution': institution,
         'session': session}))

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
    setup_status, error_chk_detail = error_check_logic.Checker().Run(institution, session)

    template_values = {
      'logout_url': auth.GetLogoutUrl(self),
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'setup_status': setup_status,
      'error_chk_detail': error_chk_detail,
      'session_query': session_query,
    }
    template = JINJA_ENVIRONMENT.get_template('error_check.html')
    self.response.write(template.render(template_values))
