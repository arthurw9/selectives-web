import webapp2
import logging
import json

import models
import authorizer
import logic

class HoverText(webapp2.RequestHandler):

  def post(self):
    auth = authorizer.Authorizer(self)
    if not auth.HasStudentAccess():
      self.response.status = 403 # Forbidden
      return

    institution = self.request.get("institution")
    if not institution:
      logging.fatal("no institution")
    session = self.request.get("session")
    if not session:
      logging.fatal("no session")

    if not auth.HasPageAccess(institution, session, "schedule"):
      self.response.status = 403 # Forbidden
      return

    class_ids = self.request.get("class_ids")
    class_ids = json.loads(class_ids)
    results = {}
    classes = models.Classes.FetchJson(institution, session)
    classes_by_id = {}
    for c in classes:
      classes_by_id[c['id']] = c
    for class_id in class_ids:
      results[str(class_id)] = logic.GetHoverText(institution, session, False, classes_by_id[int(class_id)])
    self.response.write(json.dumps(results))
