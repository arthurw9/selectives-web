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


class Parser(object):

  def __init__(self, dayparts):
    self.string = dayparts
    self.yaml = yaml.load(dayparts.lower())

  def isValid(self):
    if not isinstance(self.yaml, list):
      err_msg = "# Dayparts should be a list not %s\n" % type(self.yaml)
      self.string = err_msg + self.string
      return False
    for d in self.yaml:
      if not isinstance(d, str):
        err_msg = "# %s should be a string not %s\n" % (d, type(d))
        self.string = err_msg + self.string
        return False
    return True

  def normalize(self):
    if self.isValid():
      return yaml.dump(self.yaml, default_flow_style=False)
    else:
      return self.string


class Dayparts(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/dayparts?%s" % urllib.urlencode(
        {'message': message, 
         'institution': institution,
         'session': session}))

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
    dayparts = self.request.get("dayparts")
    if not dayparts:
      logging.fatal("no dayparts")
    dayparts = str(Parser(dayparts).normalize())
    models.Dayparts.store(institution, session, dayparts)
    self.RedirectToSelf(institution, session, "saved dayparts")

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

    logout_url = auth.GetLogoutUrl(self)
    message = self.request.get('message')
    session_query = urllib.urlencode({'institution': institution,
                                      'session': session})
    dayparts = models.Dayparts.fetch(institution, session)
    if not dayparts:
      dayparts = '\n'.join([
          "# Sample data. Lines with leading # signs are comments.",
          "# Change the data below.",
          "- monday am",
          "- Tuesday pm",])

    template_values = {
      'logout_url': logout_url,
      'user' : auth.user,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'dayparts': dayparts,
      'self': self.request.uri,
    }
    template = JINJA_ENVIRONMENT.get_template('dayparts.html')
    self.response.write(template.render(template_values))


application = webapp2.WSGIApplication([
  ('/dayparts', Dayparts),
], debug=True)
