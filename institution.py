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
    auth = authorizer.Authorizer()
    if auth.ShouldRedirect(self):
      auth.Redirect(self)
      return

    institution = self.request.get("institution")
    action = self.request.get("action");
    if action == "add_admin":
      email = self.request.get("administrator")
      models.Admin.storeInstitutionAdmin(institution, email)
      self.RedirectToSelf(institution, 'added admin %s' % email)
      return

    if action == "delete_admin":
      msgs = []
      administrators = self.request.get("administrator", allow_multiple=True)
      for email in administrators:
        msgs.append(email)
        models.Admin.deleteInstitutionAdmin(institution, email)
      self.RedirectToSelf(institution, 'deleted admins %s' % ','.join(msgs))
      return

    if action == "add_session":
      name = self.request.get("session")
      logging.info('zzz session: %s, institution: %s' % (name, institution))
      models.Session.store(institution, name)
      self.RedirectToSelf(institution, 'added session %s' % name)
      return

  def get(self):
    auth = authorizer.Authorizer()
    if auth.ShouldRedirect(self):
      auth.Redirect(self)
      return

    institution = self.request.get("institution")
    administrators = models.Admin.FetchAllInstitutionAdmins(institution)
    administrators = [x.email for x in administrators]

    sessions = models.Session.FetchAllSessions(institution)
    sessions_and_urls = []
    for session in sessions:
      args = urllib.urlencode({'institution': institution,
                               'session': session.name})
      sessions_and_urls.append(
          {'name': session.name,
           'url': ('/dayparts?%s' % args)})

    message = self.request.get('message')

    logout_url = auth.GetLogoutUrl(self)

    template_values = {
      'logout_url': logout_url,
      'user' : auth.user,
      'institution' : institution,
      'sessions' : sessions_and_urls,
      'administrators' : administrators,
      'message': message,
    }
    template = JINJA_ENVIRONMENT.get_template('institution.html')
    self.response.write(template.render(template_values))


application = webapp2.WSGIApplication([
  ('/institution', Institution),
], debug=True)
