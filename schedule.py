import os
import urllib
import jinja2
import webapp2
import logging
import yaml

import models
import authorizer
import logic

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class Schedule(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, student, message):
    self.redirect("/schedule?%s" % urllib.urlencode(
        {'message': message, 
         'student': student,
         'institution': institution,
         'session': session}))

  def post(self):
    auth = authorizer.Authorizer(self)
    if not auth.HasStudentAccess():
      auth.Redirect()
      return

    institution = self.request.get("institution")
    if not institution:
      logging.fatal("no institution")
    session = self.request.get("session")
    if not session:
      logging.fatal("no session")
    email = auth.student_email
    # TODO: what are we saving? Let's save it here.
    if self.request.get("Save") == "Save":
      logging.info("Form Saved")
    else:
      logging.info("Auto Save")
    self.RedirectToSelf(institution, session, email, "Saved Preferences")

  def get(self):
    auth = authorizer.Authorizer(self)
    if not auth.HasStudentAccess():
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
    email = auth.student_email

    dayparts = yaml.load(models.Dayparts.fetch(institution, session))
    if not dayparts:
      dayparts = []
    classes = models.Classes.Fetch(institution, session)
    classes = yaml.load(classes)
    try:
      _ = [c for c in classes]
    except TypeError:
      classes = []
    classes_by_daypart = {}
    eligible_classes = logic.EligibleClassIdsForStudent(
        auth.student_entity, classes)
    for daypart in dayparts:
      classes_by_daypart[daypart] = []
    for c in classes:
      class_id = str(c['id'])
      if class_id not in eligible_classes:
        continue
      for daypart in [s['daypart'] for s in c['schedule']]:
        classes_by_daypart[daypart].append(c)
    
    schedule = models.Schedule.Fetch(institution, session, email)

    template_values = {
      'logout_url': auth.GetLogoutUrl(self),
      'user' : auth.user,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'student': auth.student_entity,
      'dayparts': dayparts,
      'classes_by_daypart': classes_by_daypart,
      'schedule': schedule,
    }
    template = JINJA_ENVIRONMENT.get_template('schedule.html')
    self.response.write(template.render(template_values))
