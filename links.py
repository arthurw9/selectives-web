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


class Links(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/links?%s" % urllib.urlencode(
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
    links = self.request.get("links")
    if not links:
      logging.fatal("no links")
    links = schemas.Links().Update(links)
    models.Links.store(institution, session, links)
    error_check_logic.Checker.setStatus(institution, session, 'UNKNOWN')
    self.RedirectToSelf(institution, session, "saved links")

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
    links = models.Links.Fetch(institution, session)
    if not links:
      links = '\n'.join([
          "# Sample data. Lines with leading # signs are comments.",
          "# Change the data below.",
          "- name: 7th Grade Schedule",
          "  url: https://drive.google.com/drive/folders/0B16740tCYESsUHd3T3NIY00wcWc",
          "- name: 8th Grade Schedule",
          "  url: https://drive.google.com/drive/folders/0B16740tCYESsUHd3T3NIY00wcWc",])

    template_values = {
      'institution' : institution,
      'session' : session,
      'message': message,
      'setup_status': setup_status,
      'session_query': session_query,
      'links': links,
      'self': self.request.uri,
    }
    template = JINJA_ENVIRONMENT.get_template('links.html')
    self.response.write(template.render(template_values))
