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
    "- email: UNIQUE\n"
    "  first: REQUIRED\n"
    "  last: REQUIRED\n"
    "  current_grade: REQUIRED\n"
    "  current_homeroom: REQUIRED\n")


class Students(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/students?%s" % urllib.urlencode(
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
    students = self.request.get("students")
    if not students:
      logging.warning("no students")
    students = schema.Update(students)
    logging.info("posted students %s", students)
    models.Students.store(institution, session, students)
    self.RedirectToSelf(institution, session, "saved students")

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
    students = models.Students.fetch(institution, session)
    if not students:
      students = '\n'.join([
          "# Sample data. Lines with leading # signs are comments.",
          "# Change the data below.",
          "- email: student1@mydiscoveryk8.org",
          "  first: Stu",
          "  last: Dent1",
          "  current_grade: 8",
          "  current_homeroom: 29",
          "- email: student2@mydiscoveryk8.org",
          "  first: Stu",
          "  last: Dent2",
          "  current_grade: 7",
          "  current_homeroom: 19",
          "- email: student3@mydiscoveryk8.org",
          "  first: Stu",
          "  last: Dent3",
          "  current_grade: 6",
          "  current_homeroom: 23",])

    template_values = {
      'logout_url': logout_url,
      'user' : auth.user,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'students': students,
      'self': self.request.uri,
    }
    template = JINJA_ENVIRONMENT.get_template('students.html')
    self.response.write(template.render(template_values))
