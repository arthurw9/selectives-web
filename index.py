import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


GLOBAL_KEY = ndb.Key("global", "global")


class Admin(ndb.Model):
  """Models an individual Guestbook entry with content and date."""
  email = ndb.StringProperty()


def admin_key(email):
  return ndb.Key("global", "global", Admin, email);


class Institution(ndb.Model):
  """Models an individual Guestbook entry with content and date."""
  name = ndb.StringProperty()


def institution_key(name):
  return ndb.Key("global", "global", Institution, name)

# TODO: figure out what the user has access to and take them there.
# TODO: Make the links to the Institution work.

class Index(webapp2.RequestHandler):
  
  def post(self):
    user = users.get_current_user()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return

    action = self.request.get("action");
    if action == "add_admin":
      email = self.request.get("administrator")
      Admin(email=email, key=admin_key(email)).put()
      self.redirect("/?%s" % urllib.urlencode({'message': 'added user: ' + email}))
      return

    if action == "delete_admin":
      msgs = []
      administrators = self.request.get("administrator", allow_multiple=True)
      for email in administrators:
        msgs.append(email)
        admin_key(email).delete()
      self.redirect("/?%s" % urllib.urlencode({'message': 'delete users: ' + ','.join(msgs)}))
      return

    if action == "add_institution":
      name = self.request.get("institution")
      Institution(name=name, key=institution_key(name)).put()
      self.redirect("/?%s" % urllib.urlencode({'message': 'added institution: ' + name}))
      return

  def get(self):
    user = users.get_current_user()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return

    administrators = Admin.query(ancestor=GLOBAL_KEY).fetch()
    administrators = [x.email for x in administrators]

    institutions = Institution.query(ancestor=GLOBAL_KEY).fetch()
    institutions_and_urls = []
    for institution in institutions:
      args = urllib.urlencode({'institution': institution.name })
      institutions_and_urls.append(
          {'name': institution.name, 'url': '/?%s' % args})

    message = self.request.get('message')

    logout_url = users.create_logout_url(self.request.uri)

    template_values = {
      'logout_url': logout_url,
      'user' : user,
      'institutions' : institutions_and_urls,
      'administrators' : administrators,
      'message': message,
    }
    template = JINJA_ENVIRONMENT.get_template('index.html')
    self.response.write(template.render(template_values))


application = webapp2.WSGIApplication([
  ('/', Index),
], debug=True)
