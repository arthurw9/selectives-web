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
import preferences_admin
import scheduler
import groups_classes
import schedule
import groups_students

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
  ('/schedule', schedule.Schedule),
  ('/preferences_admin', preferences_admin.PreferencesAdmin),
  ('/scheduler', scheduler.Scheduler),
  ('/groups_classes', groups_classes.GroupsClasses),
  ('/groups_students', groups_students.GroupsStudents),
], debug=True)
