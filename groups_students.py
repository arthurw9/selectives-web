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

class GroupsStudents(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/groups_students?%s" % urllib.urlencode(
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
    groups_students = self.request.get("groups_students")
    if not groups_students:
      logging.fatal("no groups students")
    groups_students = schemas.student_groups.Update(groups_students)
    models.GroupsStudents.store(institution, session, groups_students)
    error_check_logic.Checker.setStatus(institution, session, 'UNKNOWN')
    self.RedirectToSelf(institution, session, "saved groups students")

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
    groups_students = models.GroupsStudents.Fetch(institution, session)
    if not groups_students:
      groups_students = '\n'.join([
          "# Sample data. Lines with leading # signs are comments.",
          "# Change the data below.",
          "- group_name: TLC",
          "  emails:",
          "    - zmeydbray@gmail.com",
          "    - vmeydbray@gmail.com",
          "    - tmeydbray@gmail.com"])

    template_values = {
      'logout_url': logout_url,
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'setup_msg': setup_msg,
      'session_query': session_query,
      'groups_students': groups_students,
      'self': self.request.uri,
    }
    template = JINJA_ENVIRONMENT.get_template('groups_students.html')
    self.response.write(template.render(template_values))
