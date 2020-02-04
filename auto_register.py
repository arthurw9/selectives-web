import os
import urllib
import jinja2
import webapp2
import logging
import yayv
import schemas
import error_check_logic
import models
import authorizer
import logic

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

dayOrder = ['Mon A', 'Mon B', 'Tues A', 'Tues B',
            'Thurs A', 'Thurs B', 'Fri A', 'Fri B']

def listOrder(c):
  if 'instructor' in c:
    return (c['name'],
            dayOrder.index(c['schedule'][0]['daypart']),
            c['instructor'])
  else:
    return (c['name'],
            dayOrder.index(c['schedule'][0]['daypart']))

class AutoRegister(webapp2.RequestHandler):

  def RedirectToSelf(self, institution, session, message):
    self.redirect("/auto_register?%s" % urllib.urlencode(
        {'message': message, 
         'institution': institution,
         'session': session}))

  def Save(self, institution, session, auto_register):
    auto_register = schemas.AutoRegister().Update(auto_register)
    models.AutoRegister.store(institution, session, auto_register)
    error_check_logic.Checker.setStatus(institution, session, 'UNKNOWN')

  def AutoRegister(self, institution, session, auto_register):
    auto_register = models.AutoRegister.FetchJson(institution, session)
    students = models.Students.FetchJson(institution, session)
    for auto_class in auto_register:
      class_id = str(auto_class['class_id'])
      if (auto_class['applies_to'] == []): # applies to all students
        for s in students:
          if not ('exempt' in auto_class and s['email'] in auto_class['exempt']):
            logic.AddStudentToClass(institution, session, s['email'], class_id)
      for grp in auto_class['applies_to']:
        if 'current_grade' in grp:
          for s in students:
            if (s['current_grade'] == grp['current_grade']):
              if not ('exempt' in auto_class and s['email'] in auto_class['exempt']):
                logic.AddStudentToClass(institution, session, s['email'].lower(), class_id)
        if 'group' in grp:
          student_groups = models.GroupsStudents.FetchJson(institution, session)
          for sg in student_groups:
            if (sg['group_name'] == grp['group']):
              for s_email in sg['emails']:
                if not ('exempt' in auto_class and s_email in auto_class['exempt']):
                  logic.AddStudentToClass(institution, session, s_email.lower(), class_id)
        if 'email' in grp:
          # We have no way to prevent an exempt field here, so we should check for it.
          # But there really is no point to an exempt field when applies_to is email.
          if not ('exempt' in auto_class and grp['email'] in auto_class['exempt']):
            logic.AddStudentToClass(institution, session, grp['email'].lower(), class_id)

  def post(self):
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
    auto_register = self.request.get("auto_register")
    if not auto_register:
      logging.fatal("no auto registrations")
    action = self.request.get("action")
    if action == "Save":
      self.Save(institution, session, auto_register)
    if action == "Register":
      self.Save(institution, session, auto_register)
      self.AutoRegister(institution, session, auto_register)
    self.RedirectToSelf(institution, session, "saved auto registrations")

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
    setup_status = error_check_logic.Checker.getStatus(institution, session)
    auto_register = models.AutoRegister.Fetch(institution, session)
    if not auto_register:
      auto_register = '\n'.join([
          "# Sample data. Lines with leading # signs are comments.",
          "# Change the data below.",
          "- class: 6th Core",
          "  class_id: 65",
          "  applies_to:",
          "    - current_grade: 6",
          "  exempt:",
          "    - student3@mydiscoveryk8.org",
          "- class: 7th Core",
          "  class_id: 63",
          "  applies_to:",
          "    - current_grade: 7",
          "- class: 8th Core",
          "  class_id: 64",
          "  applies_to:",
          "    - current_grade: 8"])

    classes = models.Classes.FetchJson(institution, session)
    if classes:
      classes.sort(key=listOrder)
    for c in classes:
      r = models.ClassRoster.FetchEntity(institution, session, c['id'])
      c['num_enrolled'] = len(r['emails'])

    students = models.Students.FetchJson(institution, session)
    grades_dict = {}
    for s in students:
      grade = s['current_grade']
      grades_dict[grade] = grades_dict.get(grade, 0) + 1
      grades_dict['All'] = grades_dict.get('All', 0) + 1
    grades = []
    for g in sorted(grades_dict, reverse=True):
      grades.append([g, grades_dict[g]])

    groups = models.GroupsStudents.FetchJson(institution, session)
    if groups:
      groups.sort(key=lambda g: g['group_name'])
    for g in groups:
      g['num_students'] = len(g['emails'])

    template_values = {
      'user_email' : auth.email,
      'institution' : institution,
      'session' : session,
      'message': message,
      'setup_status': setup_status,
      'session_query': session_query,
      'auto_register': auto_register,
      'classes': classes,
      'grades': grades,
      'groups': groups,
      'self': self.request.uri,
    }
    template = JINJA_ENVIRONMENT.get_template('auto_register.html')
    self.response.write(template.render(template_values))
