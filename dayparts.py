import os
import urllib
import jinja2
import webapp2
import logging
import yayv
import schemas
import error_check_logic
import models
import authorizer

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


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
    dayparts = schemas.dayparts.Update(dayparts)
    models.Dayparts.store(institution, session, dayparts)
    error_check_logic.Checker.setStatus(institution, session, 'UNKNOWN')
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
    setup_status = error_check_logic.Checker.getStatus(institution, session)
    dayparts = models.Dayparts.Fetch(institution, session)
    if not dayparts:
      dayparts = '\n'.join([
          "# Sample data. Lines with leading # signs are comments.",
          "# Change the data below.",
          "- name: Mon A",
          "  row: 1",
          "  col: 1",
          "  rowspan: 1",
          "  colspan: 1",
          "- name: Tues A",
          "  row: 1",
          "  col: 2",
          "- name: Thurs A",
          "  row: 1",
          "  col: 3",
          "- name: Fri A",
          "  row: 1",
          "  col: 4",
          "- name: Mon B",
          "  row: 2",
          "  col: 1",
          "- name: Tues B",
          "  row: 2",
          "  col: 2",
          "- name: Thurs B",
          "  row: 2",
          "  col: 3",
          "- name: Fri B",
          "  row: 2",
          "  col: 4",])

    template_values = {
      'logout_url': logout_url,
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'setup_status': setup_status,
      'session_query': session_query,
      'dayparts': dayparts,
      'self': self.request.uri,
    }
    template = JINJA_ENVIRONMENT.get_template('dayparts.html')
    self.response.write(template.render(template_values))
