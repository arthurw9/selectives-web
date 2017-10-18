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


class ServingRules(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/serving_rules?%s" % urllib.urlencode(
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
    serving_rules = self.request.get("serving_rules")
    if not serving_rules:
      logging.fatal("no serving_rules")
    serving_rules = schemas.ServingRules().Update(serving_rules)
    models.ServingRules.store(institution, session, serving_rules)
    error_check_logic.Checker.setStatus(institution, session, 'UNKNOWN')
    self.RedirectToSelf(institution, session, "saved serving rules")

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
    setup_status = error_check_logic.Checker.getStatus(institution, session)
    serving_rules = models.ServingRules.Fetch(institution, session)
    if not serving_rules:
      serving_rules = '\n'.join([
          "# Sample data. Lines with leading # signs are comments.",
          "# Change the data below.",
          "- name: materials",
          "  allow:",
          "    - current_grade: 8",
          "    - current_grade: 7",
          "    - current_grade: 6",
          "- name: schedule",
          "  allow:",
          "    - current_homeroom: 25"])

    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'setup_status': setup_status,
      'session_query': session_query,
      'serving_rules': serving_rules,
      'self': self.request.uri,
    }
    template = JINJA_ENVIRONMENT.get_template('serving_rules.html')
    self.response.write(template.render(template_values))
