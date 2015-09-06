from google.appengine.api import users
import models
import logging
import urllib
import yaml


class Authorizer(object):
  """Report the user's access level and Redirect them to their start page."""

  def __init__(self, handler):
    self.user = users.get_current_user()
    self.handler = handler
    if self.user:
      models.RecentAccess.Store(self.user.email())
    else:
      models.RecentAccess.Store("anonymous")

  def IsGlobalAdmin(self):
    if not self.user:
      return False
    override=self.handler.request.get('o')
    return self.user.email() in models.GlobalAdmin.FetchAll()

  def GetAdministedInstitutionsList(self):
    if not self.user:
      return []
    if self.IsGlobalAdmin():
      institution_list = models.Institution.FetchAllInstitutions()
      return [ i.name for i in institution_list ]
    return models.Admin.GetInstitutionNames(self.user.email())

  def CanAdministerInstitutionFromUrl(self):
    if not self.user:
      return False
    if self.IsGlobalAdmin():
      return True
    institution = self.handler.request.get("institution")
    if not institution:
      return False
    if self.user.email() in models.Admin.FetchAll(institution):
      return True
    return False

  def HasStudentAccess(self):
    if not self.user:
      return False
    if self.CanAdministerInstitutionFromUrl():
      return True
    institution = self.handler.request.get("institution")
    if not institution:
      return False
    serving_session = models.ServingSession.FetchEntity(institution)
    logging.info("currently serving session = %s" % serving_session)
    session = self.handler.request.get("session")
    if serving_session.session_name != session:
      return False
    if not "/" + serving_session.login_type == self.handler.request.path:
      return False
    if self.GetStudentInfo(institution, session):
      return True
    return False

  def GetStudentInfo(self, institution, session):
    students = models.Students.fetch(institution, session)
    students = yaml.load(students)
    # is students iterable?
    try:
      _ = (e for e in students)
    except TypeError:
      return None
    for student in students:
      if self.user.email() in student['email']:
        if not 'name' in student:
          student['name'] = "Not Specified"
        if not 'current_grade' in student:
          student['current_grade'] = "Not Specified"
        return student
    return None
    
  def Redirect(self):
    # are they logged in?
    if not self.user:
      self.handler.redirect("/welcome")
      return
    if self.IsGlobalAdmin():
      logging.info("Redirecting %s to index", self.user.email())
      self.handler.redirect("/")
      return
    # are they an institution admin?
    institution_list = models.Admin.GetInstitutionNames(self.user.email())
    if len(institution_list) > 1:
      logging.info("Redirecting %s to /pickinstitution", self.user.email())
      self.handler.redirect("/pickinstitution")
      return
    if len(institution_list) > 0:
      institution = institution_list[0]
      logging.info("Redirecting %s to /institution", self.user.email())
      self.handler.redirect("/institution?%s" % urllib.urlencode(
          {'institution': institution}))
      return
    # are they a student with a serving session?
    serving_sessions = models.ServingSession.FetchAllEntities()
    for ss in serving_sessions:
      institution = ss.institution_name
      session = ss.session_name
      login_type = ss.login_type
      student_info = self.GetStudentInfo(institution, session)
      if student_info:
        logging.info("Redirecting %s to /%s", (self.user.email(), login_type))
        self.handler.redirect("/%s?%s" % (login_type, urllib.urlencode(
            {'institution': institution,
             'session': session})))
        return
    logging.info("Redirecting %s to /welcome", self.user.email())
    self.handler.redirect("/welcome")

  # TODO get rid of the unnecessary handler parameter
  def GetLogoutUrl(self, handler):
    return users.create_logout_url(self.handler.request.uri)


  def GetLoginUrl(self):
    return users.create_login_url("/")
