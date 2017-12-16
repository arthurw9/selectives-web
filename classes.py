import os
import urllib
import jinja2
import webapp2
import logging
import yaml
import yayv
import schemas
import error_check_logic
import models
import authorizer

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Classes(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/classes?%s" % urllib.urlencode(
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
    classes = self.request.get("classes")
    if not classes:
      logging.fatal("no classes")
    classes = schemas.Classes().Update(classes)
    models.Classes.store(institution, session, classes)
    
    # ClassRoster saves a copy of class info in its own jclass_obj
    # (for efficiency?). When Classes changes, make sure
    # ClassRoster's jclass_obj stays in sync by calling
    # ClassRoster.Store(). Otherwise, odd things happen.
    #
    # Also, calling ClassRoster.Store() when there are changes
    # to Classes, udpates the last_modified field. This fixes the
    # bug where last modified date on attendance sheet and student
    # schedule reports don't update when only Classes info changed
    # but no students were added or deleted.
    classes = yaml.load(classes)
    for c in classes:
      roster = models.ClassRoster.FetchEntity(institution, session, c['id'])
      if roster['emails'] != []:
        if c != roster['class_details']:
          models.ClassRoster.Store(institution, session, c, ",".join(roster['emails']))

    error_check_logic.Checker.setStatus(institution, session, 'UNKNOWN')
    self.RedirectToSelf(institution, session, "saved classes")

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
    classes = models.Classes.Fetch(institution, session)
    if not classes:
      classes = '\n'.join([
          "# Sample data. Lines with leading # signs are comments.",
          "# Change the data below.",
          "- name: Basket Weaving",
          "  instructor: Mr. Brown",
          "  max_enrollment: 25",
          "  schedule:",
          "    - daypart: Mon A",
          "      location: 13",
          "    - daypart: Thurs A",
          "      location: 13",
          "  prerequisites:",
          "    - current_grade: 6",
          "  description: Learn the satisfying and peaceful craft of basket weaving. You will learn under-and-over-weaving, double weaving, and the triple twist. If you like working with your hands, basket weaving can provide you with beautiful objects for your home, to give as gifts, or to sell.",
          "  donation: $10 for materials"])

    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'setup_status': setup_status,
      'session_query': session_query,
      'classes': classes,
      'self': self.request.uri,
    }
    template = JINJA_ENVIRONMENT.get_template('classes.html')
    self.response.write(template.render(template_values))
