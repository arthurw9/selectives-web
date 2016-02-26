import os
import urllib
import jinja2
import webapp2
import logging
import json

import models
import authorizer
import logic

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class CatalogPrint(webapp2.RequestHandler):
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
    if not auth.HasPageAccess(institution, session, "materials"):
      auth.RedirectTemporary(institution, session)
      return

    message = self.request.get('message')
    session_query = urllib.urlencode({'institution': institution,
                                      'session': session})
    email = auth.student_email
    classes = models.Classes.FetchJson(institution, session)
    try:
      _ = [c for c in classes]
    except TypeError:
      classes = []

    eligible_classes = logic.EligibleClassIdsForStudent(
      institution, session, auth.student_entity, classes)
    classes_for_catalog = []
    for c in classes:
      class_id = str(c['id'])
      if class_id not in eligible_classes:
        continue
      if not('exclude_from_catalog' in c and c['exclude_from_catalog']):
        classes_for_catalog.append(c)
    classes_for_catalog.sort(key=lambda c:c['name'])

    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'student': auth.student_entity,
      'classes_for_catalog': classes_for_catalog,
    }
    template = JINJA_ENVIRONMENT.get_template('catalog_print.html')
    self.response.write(template.render(template_values))
