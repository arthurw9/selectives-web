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

  def __init__(self, requirements):
    self.string = requirements
    self.yaml = yaml.load(requirements.lower())

  def isValid(self):
    if not isinstance(self.yaml, list):
      err_msg = "# Requirements should be a list not %s\n" % type(self.yaml)
      self.string = err_msg + self.string
      return False
    for d in self.yaml:
      if not isinstance(d, str):
        err_msg = "# %s should be a string not %s\n" % (d, type(d))
        self.string = err_msg + self.string
        return False
    return True

  def normalize(self):
    if self.isValid():
      return yaml.dump(self.yaml, default_flow_style=False)
    else:
      return self.string


class Requirements(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/requirements?%s" % urllib.urlencode(
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
    requirements = self.request.get("requirements")
    if not session:
      logging.fatal("no requirements")
    requirements = str(Parser(requirements).normalize())
    models.Requirements.store(institution, session, requirements)
    self.RedirectToSelf(institution, session, "saved requirements")

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
    requirements = models.Requirements.fetch(institution, session)
    if not requirements:
      requirements = '\n'.join([
          "# Sample data. Lines with leading # signs are comments.",
          "# Change the data below.",
          "- applies_to:",
          "    current_grade: 6",
          "  exempt:",
          "    - email: sarah.moffatt@mydiscoveryk8.org",
          "  class_options:",
          "    - 6th Grade Core",
          "- applies_to:",
          "  exempt:",
          "    - email: zoya@mydiscoveryk8.org",
          "    - email: alyssa@mydiscoveryk8.org",
          "  class_options:",
          "    -",
          "      - PE_Mon_or_Tue",
          "      - PE_Thu_or_Fri",
          "    - PE_2_day_equivalent # example: dance meets twice a week",
          "    -",
          "      - PE_1_day_equivalent",
          "      - PE_1_day_equivalent",])

    template_values = {
      'logout_url': logout_url,
      'user' : auth.user,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'requirements': requirements,
      'self': self.request.uri,
    }
    template = JINJA_ENVIRONMENT.get_template('requirements.html')
    self.response.write(template.render(template_values))


application = webapp2.WSGIApplication([
  ('/requirements', Requirements),
], debug=True)
