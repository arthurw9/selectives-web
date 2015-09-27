import webapp2

import index
import welcome
import institution
import dayparts
import classes
import students
import requirements
import verification
import preferences
import groups_classes

application = webapp2.WSGIApplication([
  ('/', index.Index),
  ('/welcome', welcome.Welcome),
  ('/institution', institution.Institution),
  ('/dayparts', dayparts.Dayparts),
  ('/classes', classes.Classes),
  ('/students', students.Students),
  ('/requirements', requirements.Requirements),
  ('/verification', verification.Verification),
  ('/preferences', preferences.Preferences),
  ('/groups_classes', groups_classes.GroupsClasses)
], debug=True)
