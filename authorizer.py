import Cookie
import os
import logging
try:
  from google.appengine.api import users
except:
  logging.info("google.appengine.api.users not found. "
                "We must be running in a unit test.")
import logic
import models
import urllib
import yaml


class Authorizer(object):
  """Report the user's access level and Redirect them to their start page."""

  def __init__(self, handler):
    self.handler = handler
    self.email = False
    if users.get_current_user():
      self.email = users.get_current_user().email().lower() # google capitalizes email addresses sometimes
      models.RecentAccess.Store(self.email)
    else:
      models.RecentAccess.Store("anonymous")

  def IsGlobalAdmin(self):
    if not self.email:
      return False
    return self.email in models.GlobalAdmin.FetchAll()
    #return True  #Toggle with previous line
    # to create a Global Admin on the Admin page.
    # Otherwise on a new instance, you can't get into the system!

  def GetAdministedInstitutionsList(self):
    if not self.email:
      return []
    if self.IsGlobalAdmin():
      institution_list = models.Institution.FetchAllInstitutions()
      return [ i.name for i in institution_list ]
    return models.Admin.GetInstitutionNames(self.email)

  def CanAdministerInstitutionFromUrl(self):
    if not self.email:
      return False
    if self.IsGlobalAdmin():
      return True
    institution = self.handler.request.get("institution")
    if not institution:
      return False
    if self.email in models.Admin.FetchAll(institution):
      return True
    return False

  # Administrators can impersonate students by adding student email to the url:
  # * url?student=email@domain
  # The possibly impersonated student email is exported from this class as:
  # * auth.student_email
  def HasStudentAccess(self):
    if not self.email:
      logging.error("No user")
      return False
    institution = self.handler.request.get("institution")
    if not institution:
      logging.error("No institution")
      return False
    session = self.handler.request.get("session")
    if not session:
      logging.error("No session")
      return False
    if self.CanAdministerInstitutionFromUrl():
      return self._VerifyStudent(institution,
                                 session,
                                 self.handler.request.get("student").lower())
    if not self._VerifyServingSession(institution, session):
      return False
    return self._VerifyStudent(institution,
                               session,
                               self.email)

  def HasTeacherAccess(self):
    if not self.email:
      logging.error("No user")
      return False
    institution = self.handler.request.get("institution")
    if not institution:
      logging.error("No institution")
      return False
    session = self.handler.request.get("session")
    if not session:
      logging.error("No session")
      return False
    if self.CanAdministerInstitutionFromUrl():
      return self._VerifyTeacher(institution,
                                 session,
                                 self.handler.request.get("teacher").lower())
    if not self._VerifyServingSession(institution, session):
      return False
    return self._VerifyTeacher(institution,
                               session,
                               self.email)

  def _VerifyServingSession(self, institution, session):
    serving_session = models.ServingSession.FetchEntity(institution)
    logging.info("currently serving session = %s" % serving_session)
    if serving_session.session_name == session:
      return True
    logging.error("serving session doesn't match")
    return False

  def HasPageAccess(self, institution, session, current_page):
    serving_rules = models.ServingRules.FetchJson(institution, session)
    page_types = logic.StudentAllowedPageTypes(
            institution, session, self.student_entity, serving_rules)
    if current_page in page_types:
      return True
    if self.CanAdministerInstitutionFromUrl():
      # Needed for impersonation page
      return True
    return False

  def GetStartPage(self, institution, session):
    serving_rules = models.ServingRules.FetchJson(institution, session)
    page_types = logic.StudentAllowedPageTypes(
             institution, session, self.student_entity, serving_rules)
    # When a student is listed under multiple serving rules,
    # return the start page with highest priority.
    if "schedule" in page_types:
      return "schedule"
    if "final" in page_types:
      return "postregistration"
    else:
      return "preregistration"

  def _VerifyStudent(self, institution, session, student_email):
    # returns true on success
    students = models.Students.FetchJson(institution, session)
    student_entity = logic.FindUser(student_email, students)
    if student_entity:
      self.student_email = student_email
      self.student_entity = student_entity
      return True
    logging.error("student not found '%s'" % student_email)
    return False

  def _VerifyTeacher(self, institution, session, teacher_email):
    # returns true on success
    teachers = models.Teachers.FetchJson(institution, session)
    teacher_entity = logic.FindUser(teacher_email, teachers)
    if teacher_entity:
      self.teacher_email = teacher_email
      self.teacher_entity = teacher_entity
      return True
    logging.error("teacher not found '%s'" % teacher_email)
    return False

  def Redirect(self):
    # are they logged in?
    if not self.email:
      self.handler.redirect("/welcome")
      return
    if self.IsGlobalAdmin():
      logging.info("Redirecting %s to index", self.email)
      self.handler.redirect("/")
      return
    # are they an institution admin?
    institution_list = models.Admin.GetInstitutionNames(self.email)
    if len(institution_list) > 1:
      logging.info("Redirecting %s to /pickinstitution", self.email)
      self.handler.redirect("/pickinstitution")
      return
    if len(institution_list) > 0:
      institution = institution_list[0]
      logging.info("Redirecting %s to /institution", self.email)
      self.handler.redirect("/institution?%s" % urllib.urlencode(
          {'institution': institution}))
      return
    # are they a student with a serving session?
    serving_sessions = models.ServingSession.FetchAllEntities()
    for ss in serving_sessions:
      institution = ss.institution_name
      session = ss.session_name
      verified = self._VerifyStudent(institution,
                                     session,
                                     self.email)
      if verified:
        start_page = self.GetStartPage(institution, session)
        logging.info("Redirecting %s to /%s" % (self.email, start_page))
        self.handler.redirect("/%s?%s" % (start_page, urllib.urlencode(
            {'institution': institution,
             'session': session})))
        return
    # are they a teacher with a serving session?
    for ss in serving_sessions:
      institution = ss.institution_name
      session = ss.session_name
      start_page = "error_registration"
      verified = self._VerifyTeacher(institution,
                                     session,
                                     self.email)
      if verified:
        logging.info("Redirecting %s to /%s" % (self.email, start_page))
        self.handler.redirect("/%s?%s" % (start_page, urllib.urlencode(
            {'institution': institution,
             'session': session})))
        return
    logging.info("Redirecting %s to /welcome", self.email)
    self.handler.redirect("/welcome")

  def RedirectTemporary(self, institution, session):
    self.handler.redirect("/coming_soon?%s" % urllib.urlencode(
        {'institution': institution,
         'session': session}))

# TODO get rid of the unnecessary handler parameter.
# We really want the request, not the handler, and we could get it from WebApp2.

  def GetLoginUrl(self):
    return users.create_login_url("/")
