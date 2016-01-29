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

# TODO: To reduce potential for human error,
# this is a great page to use a GUI selector
# to pick classes that belong in each group.
class GroupsClasses(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/groups_classes?%s" % urllib.urlencode(
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
    groups_classes = self.request.get("groups_classes")
    if not groups_classes:
      logging.fatal("no groups classes")
    groups_classes = schemas.ClassGroups().Update(groups_classes)
    models.GroupsClasses.store(institution, session, groups_classes)
    error_check_logic.Checker.setStatus(institution, session, 'UNKNOWN')
    self.RedirectToSelf(institution, session, "saved groups classes")

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
    groups_classes = models.GroupsClasses.Fetch(institution, session)
    if not groups_classes:
      groups_classes = '\n'.join([
          "# Sample data. Lines with leading # signs are comments.",
          "# Change the data below.",
          "- name: PE_1_day_equivalent",
          "  classes:",
          "    - name: Basketball",
          "      id: 11",
          "    - name: Basketball",
          "      id: 19",
          "    - name: Boxing",
          "      id: 33",
          "    - name: Circuit Training (Beg)",
          "      id: 12",
          "    - name: Circuit Training (Beg)",
          "      id: 43",
          "    - name: Circuit Training (Adv)",
          "      id: 32",
          "    - name: Fitness & Fun",
          "      id: 18",
          "    - name: Walking Club",
          "      id: 50",
          "- name: PE_2_day_equivalent",
          "  classes:",
          "    - name: Dance",
          "      id: 37",
          "- name: PE_Mon_or_Tue",
          "  classes:",
          "    - id: 52",
          "    - id: 53",
          "    - id: 54",
          "    - id: 55",
          "    - id: 56",
          "    - id: 57",
          "    - id: 58",
            "- name: PE_Thu_or_Fri",
          "  classes:",
          "    - id: 59",
          "    - id: 60",
          "    - id: 61",
          "    - id: 62",
          "    - id: 63",
          "    - id: 64",
          "    - id: 65",
          "    - id: 66"])

    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'setup_status': setup_status,
      'session_query': session_query,
      'groups_classes': groups_classes,
      'self': self.request.uri,
    }
    template = JINJA_ENVIRONMENT.get_template('groups_classes.html')
    self.response.write(template.render(template_values))
