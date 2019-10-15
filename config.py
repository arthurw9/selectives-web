import os
import urllib
import jinja2
import webapp2
import logging
import schemas
import error_check_logic
import models
import authorizer

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class Config(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/config?%s" % urllib.urlencode(
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
    displayRoster = self.request.get("displayRoster")
    if not displayRoster:
      logging.fatal("no displayRoster")
    htmlDesc = self.request.get("htmlDesc")
    if not htmlDesc:
      logging.fatal("no htmlDesc")
    twoPE = self.request.get("twoPE")
    if not twoPE:
      logging.fatal("no twoPE")
    logging.info("*********************")
    logging.info(twoPE)
    models.Config.store(institution, session, displayRoster, htmlDesc, twoPE)
    error_check_logic.Checker.setStatus(institution, session, 'UNKNOWN')
    self.RedirectToSelf(institution, session, "saved config")

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
    db_version = models.DBVersion.Fetch(institution, session)
    config = models.Config.Fetch(institution, session)
    displayRoster = config['displayRoster']
    htmlDesc = config['htmlDesc']
    twoPE = config['twoPE']

    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'setup_status': setup_status,
      'session_query': session_query,
      'displayRoster': displayRoster,
      'htmlDesc': htmlDesc,
      'twoPE': twoPE,
      'db_version': db_version,
      'self': self.request.uri,
    }
    template = JINJA_ENVIRONMENT.get_template('config.html')
    self.response.write(template.render(template_values))
