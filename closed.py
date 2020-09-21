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


class Closed(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/closed?%s" % urllib.urlencode(
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
    closed_msg = self.request.get("closed")
    if not closed_msg:
      logging.fatal("no temporarily closed messsage")
    models.Closed.store(institution, session, closed_msg)
    error_check_logic.Checker.setStatus(institution, session, 'UNKNOWN')
    self.RedirectToSelf(institution, session, "saved temporarily closed message")

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

    closed = models.Closed.Fetch(institution, session)
    if not closed:
      closed = '\n'.join([
        "<!-- Sample Temporarily Closed Message -->",
        "<!-- Change the text below -->",
        "<h3>Page temporarily not available</h3>",
        "<p>If registration has started, this page may be unavailable for the following reasons:"
        "<ul><li>You won the lottery! Go to <i>Step 3 - Final Schedule</i> to confirm that your schedule is complete.</li>"
        "<li>The selective team is currently working on the lottery. This page will open shortly.</li>"
        "<li>If everyone in your class can view this page except you, something might be wrong. Please talk to your teacher immediately.</li></ul>"
        "Otherwise, registration either has not started or has finished. Please double check the registration dates in <i>Step 1 - Materials</i>.</p>",])
    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'setup_status': setup_status,
      'session_query': session_query,
      'closed': closed,
      'self': self.request.uri,
    }
    template = JINJA_ENVIRONMENT.get_template('closed.html')
    self.response.write(template.render(template_values))
