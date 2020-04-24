import os
import urllib
import jinja2
import webapp2

import models
import authorizer

# Since we are inside the report directory, but Jinja doesn't allow
# {% extends '../menu.html' %}, call os.path.dirname(os.path.dirname())
# to go up to the parent directory.
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(os.path.dirname(__file__))),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

def listOrder(c):
  if 'instructor' in c:
    return (c['name'],
            c['dayorder'],
            c['instructor'])
  else:
    return (c['name'],
            c['dayorder'])

class Label(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/report/label?%s" % urllib.urlencode(
        {'message': message,
         'institution': institution,
         'session': session}))

  def get(self):
    auth = authorizer.Authorizer(self)
    if not (auth.CanAdministerInstitutionFromUrl() or
            auth.HasTeacherAccess()):
      auth.Redirect()
      return

    user_type = 'None'
    if auth.CanAdministerInstitutionFromUrl():
      user_type = 'Admin'
    elif auth.HasTeacherAccess():
      user_type = 'Teacher'

    institution = self.request.get("institution")
    if not institution:
      logging.fatal("no institution")
    session = self.request.get("session")
    if not session:
      logging.fatal("no session")

    message = self.request.get('message')
    session_query = urllib.urlencode({'institution': institution,
                                      'session': session})

    classes = models.Classes.FetchJson(institution, session)
    dayparts = models.Dayparts.FetchJson(institution, session)
    dp_dict = {} # used for ordering by col then row
    for dp in dayparts:
      dp_dict[dp['name']] = str(dp['col'])+str(dp['row'])
    for c in classes:
      c['dayorder'] = dp_dict[c['schedule'][0]['daypart']]
    if classes:
      classes.sort(key=listOrder)
    template_values = {
      'user_email' : auth.email,
      'user_type' : user_type,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'classes': classes,
    }
    template = JINJA_ENVIRONMENT.get_template('report/label.html')
    self.response.write(template.render(template_values))