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


class Index(webapp2.RequestHandler):
  
  def post(self):
    auth = authorizer.Authorizer(self)
    if not auth.IsGlobalAdmin():
      auth.Redirect()
      return

    action = self.request.get("action");
    if action == "add_admin":
      email = self.request.get("administrator")
      models.GlobalAdmin.Store(email)
      self.redirect("/?%s" % urllib.urlencode(
          {'message': 'added user: ' + email}))
      return

    if action == "delete_admin":
      msgs = []
      administrators = self.request.get("administrator", allow_multiple=True)
      for email in administrators:
        msgs.append(email)
        models.GlobalAdmin.Delete(email)
      self.redirect("/?%s" % urllib.urlencode(
          {'message': 'delete users: ' + ','.join(msgs)}))
      return

    if action == "add_institution":
      name = self.request.get("institution")
      models.Institution.store(name)
      self.redirect("/?%s" % urllib.urlencode(
          {'message': 'added institution: ' + name}))
      return

    self.redirect("/?%s" % urllib.urlencode(
          {'message': 'unrecognized command: %s' % action}))
    return

  def institutionUrl(self, institution_name):
    args = urllib.urlencode({'institution': institution_name})
    return '/institution?%s' % args

  def get(self):
    auth = authorizer.Authorizer(self)
    if not auth.IsGlobalAdmin():
      auth.Redirect()
      return

    administrators = models.GlobalAdmin.FetchAll()

    institutions = models.Institution.FetchAllInstitutions()
    institutions_and_urls = []
    for institution in institutions:
      institutions_and_urls.append(
          {'name': institution.name,
           'url': self.institutionUrl(institution.name)})

    message = self.request.get('message')

    logout_url = auth.GetLogoutUrl(self)

    template_values = {
      'logout_url': logout_url,
      'user' : auth.user,
      'institutions' : institutions_and_urls,
      'administrators' : administrators,
      'message': message,
    }
    template = JINJA_ENVIRONMENT.get_template('index.html')
    self.response.write(template.render(template_values))
