import os
import urllib
import jinja2
import webapp2
import logging
import yayv


import models
import authorizer

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


schema = yayv.ByExample(
    "- UNIQUE\n")


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
    dayparts = schema.Update(dayparts)
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
          "- Mon A",
          "- Mon B",
          "- Tues A",
          "- Tues B",
          "- Thurs A",
          "- Thurs B",
          "- Fri A",
          "- Fri B",])

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
