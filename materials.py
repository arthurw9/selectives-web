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


class Materials(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/materials?%s" % urllib.urlencode(
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
    materials = self.request.get("materials")
    if not materials:
      logging.fatal("no materials")
    models.Materials.store(institution, session, materials)
    error_check_logic.Checker.setStatus(institution, session, 'UNKNOWN')
    self.RedirectToSelf(institution, session, "saved materials")

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
    materials = models.Materials.Fetch(institution, session)
    if not materials:
      materials = '\n'.join([
        "<!-- Sample materials page -->",
        "<!-- Change the text below -->",
        "<h3>Registration Dates:</h3>",
        "<ul><li>Mon, January 1 - 8th grade</li>",
        "<li>Mon, January 8 - 7th grade</li></ul>",
        "<a href='#' target='_blank'>8th grade - Schedule of Classes</a><br>",
        "<a href='#' target='_blank'>Course Catalog</a><br>",
        "<p>Questions or feedback? Please see your teacher or email the selectives team: discovery.selectives@gmail.com</p>",])
    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'setup_status': setup_status,
      'session_query': session_query,
      'materials': materials,
      'self': self.request.uri,
    }
    template = JINJA_ENVIRONMENT.get_template('materials.html')
    self.response.write(template.render(template_values))
