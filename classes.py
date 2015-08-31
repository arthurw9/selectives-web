import os
import urllib
import jinja2
import webapp2
import logging
import yaml

import models
import authorizer

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class Parser(object):

  def __init__(self, classes):
    self.string = classes
    self.yaml = yaml.load(classes.lower())

  def normalize(self):
    return yaml.dump(self.yaml, default_flow_style=False)


class Classes(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/classes?%s" % urllib.urlencode(
        {'message': message, 
         'institution': institution,
         'session': session}))

  def post(self):
    auth = authorizer.Authorizer()
    if auth.ShouldRedirect(self):
      auth.Redirect(self)
      return

    institution = self.request.get("institution")
    if not institution:
      logging.fatal("no institution")
    session = self.request.get("session")
    if not session:
      logging.fatal("no session")
    classes = self.request.get("classes")
    if not classes:
      logging.fatal("no classes")
    classes = str(Parser(classes).normalize())
    models.Classes.store(institution, session, classes)
    self.RedirectToSelf(institution, session, "saved classes")

  def get(self):
    auth = authorizer.Authorizer()
    if auth.ShouldRedirect(self):
      auth.Redirect(self)
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
    classes = models.Classes.fetch(institution, session)
    if not classes:
      classes = '\n'.join([
          "# Sample data. Lines with leading # signs are comments.",
          "# Change the data below.",
          "- name: basket weaving",
          "  lead: mr. brown",
          "  size: 25 # max number of students",
          "  schedule:",
          "    - when: monday A",
          "      room: 13",
          "    - when: thursday B",
          "      room: 13",
          "  prerequisites:",
          "    - grade: 6"])

    template_values = {
      'logout_url': logout_url,
      'user' : auth.user,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'classes': classes,
      'self': self.request.uri,
    }
    template = JINJA_ENVIRONMENT.get_template('classes.html')
    self.response.write(template.render(template_values))


application = webapp2.WSGIApplication([
  ('/classes', Classes),
], debug=True)
