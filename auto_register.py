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


class AutoRegister(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/auto_register?%s" % urllib.urlencode(
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
    auto_register = self.request.get("auto_register")
    if not auto_register:
      logging.fatal("no auto registrations")
    auto_register = schemas.AutoRegister().Update(auto_register)
    models.AutoRegister.store(institution, session, auto_register)
    error_check_logic.Checker.setStatus(institution, session, 'UNKNOWN')
    self.RedirectToSelf(institution, session, "saved auto registrations")

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
    auto_register = models.AutoRegister.Fetch(institution, session)
    if not auto_register:
      auto_register = '\n'.join([
          "# Sample data. Lines with leading # signs are comments.",
          "# Change the data below.",
          "- class: 6th Core",
          "  class_id: 65",
          "  applies_to:",
          "    - current_grade: 6",
          "  exempt:",
          "    - student3@mydiscoveryk8.org",
          "- class: 7th Core",
          "  class_id: 63",
          "  applies_to:",
          "    - current_grade: 7",
          "- class: 8th Core",
          "  class_id: 64",
          "  applies_to:",
          "    - current_grade: 8"])

    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'setup_status': setup_status,
      'session_query': session_query,
      'auto_register': auto_register,
      'self': self.request.uri,
    }
    template = JINJA_ENVIRONMENT.get_template('auto_register.html')
    self.response.write(template.render(template_values))
