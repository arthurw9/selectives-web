import os
import urllib
import jinja2
import webapp2
import logging

import models
import authorizer

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class Institution(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, message):
    self.redirect("/institution?%s" % urllib.urlencode(
        {'message': message, 'institution': institution}))
    
  def post(self):
    auth = authorizer.Authorizer(self)
    if not auth.CanAdministerInstitutionFromUrl():
      auth.Redirect(self)
      return

    institution = self.request.get("institution")
    action = self.request.get("action");
    if action == "add_admin":
      email = self.request.get("administrator")
      models.Admin.Store(institution, email)
      self.RedirectToSelf(institution, 'added admin %s' % email)
      return

    if action == "delete_admin":
      msgs = []
      administrators = self.request.get("administrator", allow_multiple=True)
      for email in administrators:
        msgs.append(email)
        models.Admin.Delete(institution, email)
      self.RedirectToSelf(institution, 'deleted admins %s' % ','.join(msgs))
      return

    if action == "add_session":
      name = self.request.get("session")
      logging.info('adding session: %s for institution: %s' % (name, institution))
      models.Session.store(institution, name)
      self.RedirectToSelf(institution, 'added session %s' % name)
      return

    if action == "remove_session":
      name = self.request.get("session")
      logging.info('removing session: %s from institution: %s' % (name, institution))
      models.Session.delete(institution, name)
      self.RedirectToSelf(institution, 'removed session %s' % name)
      return

    if action == "enable_logins":
      name = self.request.get("session")
      login_type = self.request.get("login_type")
      logging.info('enable login: %s for session: %s from institution: %s'
                    % (login_type, name, institution))
      models.ServingSession.store(institution, name, login_type)
      self.RedirectToSelf(institution, 'enabled logins for %s' % name)
      return

    if action == "disable_logins":
      name = self.request.get("session")
      login_type = self.request.get("login_type")
      logging.info('disable login: %s for session: %s from institution: %s'
                   % (login_type, name, institution))
      models.ServingSession.delete(institution)
      self.RedirectToSelf(institution, 'disabled logins for %s %s'
                          % (login_type, name))
      return

    name = self.request.get("session")
    logging.error('Unexpected action: %s session: %s institution: %s' % ( action, name, institution))
    return

  def get(self):
    auth = authorizer.Authorizer(self)
    if not auth.CanAdministerInstitutionFromUrl():
      auth.Redirect()
      return

    institution = self.request.get("institution")

    # Hack: fixing a bug. URL parameters override posted form fields.
    # so lets get rid of the offending url parameter
    if self.request.get("session"):
      self.RedirectToSelf(institution, "hack remove session from url")
      return

    administrators = models.Admin.FetchAll(institution)

    sessions = models.Session.FetchAllSessions(institution)
    sessions_and_urls = []
    serving_session = models.ServingSession.FetchEntity(institution)
    logging.info("currently serving session = %s" % serving_session)
    for session in sessions:
      args = urllib.urlencode({'institution': institution,
                               'session': session.name})
      preferences_enabled = serving_session.login_type == "preferences"
      verification_enabled = serving_session.login_type == "verification"
      schedule_enabled = serving_session.login_type == "schedule"
      if not serving_session.session_name == session.name:
        preferences_enabled = False
        verification_enabled = False
        schedule_enabled = False
      sessions_and_urls.append(
          {'name': session.name,
           'management_url': ('/dayparts?%s' % args),
           'verification_enabled': verification_enabled,
           'preferences_enabled': preferences_enabled,
           'schedule_enabled': schedule_enabled,
          })

    message = self.request.get('message')

    logout_url = auth.GetLogoutUrl(self)

    template_values = {
      'logout_url': logout_url,
      'user_email' : auth.email,
      'institution' : institution,
      'sessions' : sessions_and_urls,
      'administrators' : administrators,
      'message': message,
    }
    template = JINJA_ENVIRONMENT.get_template('institution.html')
    self.response.write(template.render(template_values))
