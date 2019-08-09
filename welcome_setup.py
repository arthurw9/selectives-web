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


class WelcomeSetup(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/welcome_setup?%s" % urllib.urlencode(
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
    welcome_msg = self.request.get("welcome_msg")
    if not welcome_msg:
      logging.fatal("no welcome_msg")
    models.Welcome.store(welcome_msg)
    error_check_logic.Checker.setStatus(institution, session, 'UNKNOWN')
    self.RedirectToSelf(institution, session, "saved welcome message")

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
    welcome_msg = models.Welcome.Fetch()
    if not welcome_msg:
      welcome_msg = '\n'.join([
        "<!-- Sample welcome message -->",
        "<!-- Change the text below -->",
        "<h1>Welcome to Discovery Charter School Selectives!</h1>",
        "<h3>To Log In</h3>",
        "<ol>",
        "<li>First make sure you are signed into your google account.",
        "<ul>",
        "<li>Students should use their school account <em>first.last##@mydiscoveryk8.org</em></li>",
        "<li>Instructors, please contact the selectives team for access.</li>",
        "</ul></li>",
        "<li>Click on <b>Log In</b> in the top right corner.</li>",
        "<li>If prompted for permission to access your Google Account, click <b>Allow</b>.</li>",
        "</ol>",
        "<p>Questions or feedback? Please see your teacher or email the selectives team: discovery.selectives@gmail.com</p>",
        "<a href='https://www.google.com/search?tbm=isch&q=smiley+face'>Have a smiley face</a>",])

    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'setup_status': setup_status,
      'session_query': session_query,
      'welcome_msg': welcome_msg,
      'self': self.request.uri,
    }
    template = JINJA_ENVIRONMENT.get_template('welcome_setup.html')
    self.response.write(template.render(template_values))
