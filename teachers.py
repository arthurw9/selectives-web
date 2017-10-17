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


class Teachers(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/teachers?%s" % urllib.urlencode(
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
    teachers = self.request.get("teachers")
    if not teachers:
      logging.warning("no teachers")
    teachers = schemas.Teachers().Update(teachers)
    logging.info("posted teachers %s", teachers)
    models.Teachers.store(institution, session, teachers)
    error_check_logic.Checker.setStatus(institution, session, 'UNKNOWN')
    self.RedirectToSelf(institution, session, "saved teachers")

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
    teachers = models.Teachers.Fetch(institution, session)
    if not teachers:
      teachers = '\n'.join([
          "# Sample data. Lines with leading # signs are comments.",
          "# Change the data below.",
          "- email: cbauerle@discoveryk8.org",
          "  first: Carol",
          "  last: Bauerle",
          "  current_homeroom: 27",
          "- email: ddowling@discoveryk8.org",
          "  first: Dan",
          "  last: Dowling",
          "  current_homeroom: 29",])

    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'setup_status': setup_status,
      'session_query': session_query,
      'teachers': teachers,
      'self': self.request.uri,
    }
    template = JINJA_ENVIRONMENT.get_template('teachers.html')
    self.response.write(template.render(template_values))
