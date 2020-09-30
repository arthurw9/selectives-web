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
  return (c['dayorder'],
          c['name'])

class SignupCard(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/report/signup_card?%s" % urllib.urlencode(
        {'message': message,
         'institution': institution,
         'session': session}))

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

    dayparts = models.Dayparts.FetchJson(institution, session)
    dp_dict = {} # used for ordering by col then row
    for dp in dayparts:
      dp_dict[dp['name']] = str(dp['col'])+str(dp['row'])

    classes = models.Classes.FetchJson(institution, session)
    classes_to_print = []
    for c in classes:
      c['dayorder'] = dp_dict[c['schedule'][0]['daypart']]
      if 'exclude_from_catalog' not in c or c['name'] == 'PE':
        classes_to_print.append(c)
    if classes_to_print:
      classes_to_print.sort(key=listOrder)

    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'classes': classes_to_print,
    }
    template = JINJA_ENVIRONMENT.get_template('report/signup_card.html')
    self.response.write(template.render(template_values))