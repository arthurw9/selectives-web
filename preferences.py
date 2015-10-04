import os
import urllib
import jinja2
import webapp2
import logging
import yaml
import itertools

import models
import authorizer

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class Preferences(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/preferences?%s" % urllib.urlencode(
        {'message': message, 
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
    email = auth.user.email()
    want = self.request.get("want").split(",")
    dontcare = self.request.get("dontcare").split(",")
    dontwant = self.request.get("dontwant").split(",")
    models.Preferences.Store(email, institution, session,
                             want, dontcare, dontwant)
    self.RedirectToSelf(institution, session, "Saved Preferences")

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

    student_info = auth.GetStudentInfo(institution, session)
    if not student_info:
      student_info = {'name': 'Not found',
                      'current_grade': 'Not found'}
    message = self.request.get('message')
    session_query = urllib.urlencode({'institution': institution,
                                      'session': session})

    classes = models.Classes.Fetch(institution, session)
    classes = yaml.load(classes)
    try:
      _ = [c for c in classes]
    except TypeError:
      classes = []
    classes_by_id = {}
    for c in classes:
      class_id = str(c['id'])
      class_name = c['name']
      # TODO: add proper class_desc instead of just dumping the yaml
      class_desc = yaml.dump(c, default_flow_style=False)
      classes_by_id[class_id] = {'name': class_name,
                                 'description': class_desc }
    if not classes_by_id:
      classes_by_id['0'] = {'name': 'None', 'desc': 'None'}
    all_class_ids = set([str(c_id) for c_id in classes_by_id.keys()])
    # TODO: find the list of eligible classes for this student.
    eligible_class_ids = all_class_ids
    all_class_ids = all_class_ids.intersection(eligible_class_ids)

    prefs = models.Preferences.FetchEntity(
        auth.user.email(), institution, session)
    want_ids = prefs.want.split(',')
    dontcare_ids = prefs.dontcare.split(',')
    dontwant_ids = prefs.dontwant.split(',')

    new_class_ids = all_class_ids.difference(want_ids)
    new_class_ids = new_class_ids.difference(dontcare_ids)
    new_class_ids = new_class_ids.difference(dontwant_ids)
    dontcare_ids = list(new_class_ids) + dontcare_ids

    def RemoveDeletedClasses(class_ids):
      for class_id in class_ids:
        if class_id in classes_by_id:
          yield class_id

    want_ids = RemoveDeletedClasses(want_ids)
    dontwant_ids = RemoveDeletedClasses(dontwant_ids)
    template_values = {
      'logout_url': auth.GetLogoutUrl(self),
      'user' : auth.user,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'classes': classes_by_id,
      'student': student_info,
      'want_ids': want_ids,
      'dontwant_ids': dontwant_ids,
      'dontcare_ids': dontcare_ids,
    }
    template = JINJA_ENVIRONMENT.get_template('preferences.html')
    self.response.write(template.render(template_values))
