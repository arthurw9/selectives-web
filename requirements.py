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


class Requirements(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/requirements?%s" % urllib.urlencode(
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
    requirements = self.request.get("requirements")
    if not requirements:
      logging.fatal("no requirements")
    requirements = schemas.requirements.Update(requirements)
    models.Requirements.store(institution, session, requirements)
    error_check_logic.Checker.setStatus(institution, session, 'UNKNOWN')
    self.RedirectToSelf(institution, session, "saved requirements")

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
    setup_msg = error_check_logic.Checker.getStatus(institution, session)
    requirements = models.Requirements.Fetch(institution, session)
    if not requirements:
      requirements = '\n'.join([
          "# Sample data. Lines with leading # signs are comments.",
          "# Change the data below.",
          "- name: PE_REQUIREMENT",
          "  applies_to: []",
          "  exempt:",
          "    - student1@mydiscoveryk8.org",
          "    - student2@mydiscoveryk8.org",
          "  class_or_group_options:",
          "    -",  # OR
          "      - PE_Mon_or_Tue",  # AND
          "      - PE_Thu_or_Fri",
          "    -",  # OR
          "      - PE_2_day_equivalent",
          "    -",  # OR
          "      - PE_Mon_or_Tue",  # AND
          "      - PE_1_day_equivalent",
          "    -",  # OR
          "      - PE_1_day_equivalent",  # AND
          "      - PE_Thu_or_Fri",
          "    -",  # OR
          "      - PE_1_day_equivalent",  # AND
          "      - PE_1_day_equivalent",
          "- name: CORE_6",
          "  applies_to:",
          "    - current_grade: 6",
          "  exempt:",
          "    - student3@mydiscoveryk8.org",
          "  class_or_group_options:",
          "    -",
          "      - 6th Grade Core",
          "- name: CORE_7",
          "  applies_to:",
          "    - current_grade: 7",
          "  class_or_group_options:",
          "    -",
          "      - 7th Grade Core",
          "- name: CORE_8",
          "  applies_to:",
          "    - current_grade: 8",
          "  class_or_group_options:",
          "    -",
          "      - 8th Grade Core"])

    template_values = {
      'logout_url': logout_url,
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'setup_msg': setup_msg,
      'session_query': session_query,
      'requirements': requirements,
      'self': self.request.uri,
    }
    template = JINJA_ENVIRONMENT.get_template('requirements.html')
    self.response.write(template.render(template_values))
