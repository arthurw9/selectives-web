import os
import urllib
import jinja2
import webapp2
import logging
import yayv

import models
import authorizer

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

schema = yayv.ByExample(
    "- name: REQUIRED\n"
    "  id: AUTO_INC\n"
    "  classes:\n"
    "    - OPTIONAL\n")

class GroupsClasses(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/groups_classes?%s" % urllib.urlencode(
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
    groups_classes = self.request.get("groups_classes")
    if not groups_classes:
      logging.fatal("no groups classes")
    groups_classes = schema.Update(groups_classes)
    models.GroupsClasses.store(institution, session, groups_classes)
    self.RedirectToSelf(institution, session, "saved groups classes")

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

    logout_url = auth.GetLogoutUrl(self)
    message = self.request.get('message')
    session_query = urllib.urlencode({'institution': institution,
                                      'session': session})
    groups_classes = models.GroupsClasses.fetch(institution, session)
    if not groups_classes:
      groups_classes = '\n'.join([
          "# Sample data. Lines with leading # signs are comments.",
          "# Change the data below.",
          "- name: PE Substitutes",
          "  classes:",
          "    - Basketball",
          "    - Boxing",
          "    - Circuit Training (Beg)",
          "    - Circuit Training (Adv)",
          "    - Dance",
          "    - Fitness & Fun",
          "    - Walking Club",
          "- name: STEM Classes",
          "  classes:",
          "    - Digital Media Development",
          "    - How to Save the World from Global Warming",
          "    - Lego Robotics",
          "    - My Digital Life",
          "    - Tech Challenge",
          "    - Wired!"])

    template_values = {
      'logout_url': logout_url,
      'user' : auth.user,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'groups_classes': groups_classes,
      'self': self.request.uri,
    }
    template = JINJA_ENVIRONMENT.get_template('groups_classes.html')
    self.response.write(template.render(template_values))
