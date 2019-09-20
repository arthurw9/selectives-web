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
    loader=jinja2.FileSystemLoader(os.path.dirname(os.path.dirname(__file__))),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class Courses(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/teacher/courses?%s" % urllib.urlencode(
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
    dayparts = models.Dayparts.FetchJson(institution, session)
    if not dayparts:
      dayparts = []
    classes = models.Classes.FetchJson(institution, session)
    try:
      _ = [c for c in classes]
    except TypeError:
      classes = []
    classes_by_daypart = {}
    dayparts_ordered = []

    max_row = max([daypart['row'] for daypart in dayparts])
    max_col = max([daypart['col'] for daypart in dayparts])

    # order the dayparts by row and col specified in yaml
    for row in range(max_row):
      dayparts_ordered.append([])
      for col in range(max_col):
        found_daypart = False
        for dp in dayparts:
          if dp['row'] == row+1 and dp['col'] == col+1:
            dayparts_ordered[row].append(dp['name'])
            found_daypart = True
        if found_daypart == False:
          dayparts_ordered[row].append('')
    for daypart in dayparts:
      classes_by_daypart[daypart['name']] = []
    classes_by_id = {}
    use_full_description = auth.CanAdministerInstitutionFromUrl()
    for c in classes:
      class_id = str(c['id'])
      classes_by_id[class_id] = c
      c['hover_text'] = logic.GetHoverText(institution, session, use_full_description, c)
      c['description'] = logic.GetHTMLDescription(institution, session, c)
      for daypart in [s['daypart'] for s in c['schedule']]:
        if daypart in classes_by_daypart:
          classes_by_daypart[daypart].append(c)
    for daypart in classes_by_daypart:
      classes_by_daypart[daypart].sort(key=lambda c:c['name'])

    config = models.Config.Fetch(institution, session)

    template_values = {
      'user_type' : user_type,
      'institution' : institution,
      'session' : session,
      'message': message,
      'session_query': session_query,
      'classes_by_daypart': classes_by_daypart,
      'dayparts_ordered': dayparts_ordered,
      'classes_by_id': classes_by_id,
      'html_desc': config['htmlDesc'],
    }
    template = JINJA_ENVIRONMENT.get_template('teacher/courses.html')
    self.response.write(template.render(template_values))
