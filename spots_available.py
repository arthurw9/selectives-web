import webapp2
import logging
import json

import models
import authorizer
import logic

class SpotsAvailable(webapp2.RequestHandler):

  def post(self):
    auth = authorizer.Authorizer(self)
    if not (auth.HasStudentAccess() or
            auth.HasTeacherAccess()):
      self.response.status = 403 # Forbidden
      return

    institution = self.request.get("institution")
    if not institution:
      logging.fatal("no institution")
    session = self.request.get("session")
    if not session:
      logging.fatal("no session")

    if not (auth.HasTeacherAccess() or
            auth.HasPageAccess(institution, session, "schedule")):
      self.response.status = 403 # Forbidden
      return

    class_ids = self.request.get("class_ids")
    class_ids = json.loads(class_ids)
    results = {}
    for class_id in class_ids:
      roster = models.ClassRoster.FetchEntity(institution, session, class_id)
      results[str(class_id)] = roster['remaining_space']
    self.response.write(json.dumps(results))
