from google.appengine.ext import ndb

GLOBAL_KEY = ndb.Key("global", "global")


class GlobalAdmin(ndb.Model):
  """email addresses for users with full access to the site."""
  email = ndb.StringProperty()

  @classmethod
  def global_admin_key(cls, email):
    return ndb.Key("global", "global", GlobalAdmin, email);

  @classmethod
  def Store(cls, email_addr):
    admin = GlobalAdmin(email=email_addr)
    admin.key = GlobalAdmin.global_admin_key(email_addr)
    admin.put();

  @classmethod
  def Delete(cls, email_addr):
    GlobalAdmin.global_admin_key(email_addr).delete()

  @classmethod
  def FetchAll(cls):
    return GlobalAdmin.query(ancestor=GLOBAL_KEY).fetch()


class Admin(ndb.Model):
  """email addresses for users with full access to an institution."""
  email = ndb.StringProperty()

  @classmethod
  def admin_key_partial(cls, institution):
    return ndb.Key('InstitutionKey', institution);

  @classmethod
  def admin_key(cls, institution, email):
    return ndb.Key('InstitutionKey', institution, Admin, email);

  @classmethod
  def Store(cls, institution, email_addr):
    key = Admin.admin_key(institution, email_addr)
    Admin(email=email_addr, key=key).put();

  @classmethod
  def Delete(cls, institution, email_addr):
    Admin.admin_key(institution, email_addr).delete()

  @classmethod
  def FetchAll(cls, institution):
    return Admin.query(ancestor=Admin.admin_key_partial(institution)).fetch()


class Institution(ndb.Model):
  """Institution name"""
  name = ndb.StringProperty()

  @classmethod
  def institution_key(cls, name):
    return ndb.Key("global", "global", Institution, name)

  @classmethod
  def store(cls, name):
    Institution(name=name, key=Institution.institution_key(name)).put()

  @classmethod
  def FetchAllInstitutions(cls):
    return Institution.query(ancestor=GLOBAL_KEY).fetch()


class Session(ndb.Model):
  """Session name"""
  name = ndb.StringProperty()

  @classmethod
  def session_key_partial(cls, institution):
    return ndb.Key("InstitutionKey", institution)

  @classmethod
  def session_key(cls, institution, session_name):
    return ndb.Key(Session, session_name,
                   parent=ndb.Key("InstitutionKey", institution))

  @classmethod
  def FetchAllSessions(cls, institution):
    return Session.query(
        ancestor=Session.session_key_partial(institution)).fetch()

  @classmethod
  def store(cls, institution, session_name):
    session = Session(name=session_name)
    session.key = Session.session_key(institution, session_name)
    session.put()

  @classmethod
  def delete(cls, institution, session_name):
    Session.session_key(institution, session_name).delete()


class ServingSession(ndb.Model):
  """Which session is currently serving. Empty if none."""
  session_name = ndb.StringProperty()
  login_type = ndb.StringProperty()

  @classmethod
  def serving_session_key(cls, institution):
    return ndb.Key("InstitutionKey", institution, ServingSession, "serving_session")

  @classmethod
  def fetch(cls, institution):
    ss = ServingSession.serving_session_key(institution).get()
    if ss:
      return ss
    ss = ServingSession()
    ss.key = ServingSession.serving_session_key(institution)
    return ss

  @classmethod
  def store(cls, institution, session_name, login_type):
    serving_session = ServingSession()
    serving_session.session_name = session_name
    serving_session.login_type = login_type
    serving_session.key = ServingSession.serving_session_key(institution)
    serving_session.put()

  @classmethod
  def delete(cls, institution):
    ServingSession.serving_session_key(institution).delete()


class Dayparts(ndb.Model):
  """Examples: Monday AM, or M-W-F 8am-9am"""
  data = ndb.StringProperty()

  @classmethod
  def dayparts_key(cls, institution, session):
    return ndb.Key("InstitutionKey", institution,
                   Session, session,
                   Dayparts, "dayparts")

  @classmethod
  def fetch(cls, institution, session):
    dayparts = Dayparts.dayparts_key(institution, session).get()
    if dayparts:
      return dayparts.data
    else:
      return ''

  @classmethod
  def store(cls, institution, session_name, dayparts_data):
    dayparts = Dayparts(data = dayparts_data)
    dayparts.key = Dayparts.dayparts_key(institution, session_name)
    dayparts.put()


class Classes(ndb.Model):
  """List of classes in yaml format."""
  data = ndb.StringProperty()

  @classmethod
  def classes_key(cls, institution, session):
    return ndb.Key("InstitutionKey", institution,
                   Session, session,
                   Classes, "classes")

  @classmethod
  def fetch(cls, institution, session):
    classes = Classes.classes_key(institution, session).get()
    if classes:
      return classes.data
    else:
      return ''

  @classmethod
  def store(cls, institution, session_name, classes_data):
    classes = Classes(data = classes_data)
    classes.key = Classes.classes_key(institution, session_name)
    classes.put()


class Students(ndb.Model):
  """List of students in yaml format."""
  data = ndb.StringProperty()

  @classmethod
  def students_key(cls, institution, session):
    return ndb.Key("InstitutionKey", institution,
                   Session, session,
                   Students, "students")

  @classmethod
  def fetch(cls, institution, session):
    students = Students.students_key(institution, session).get()
    if students:
      return students.data
    else:
      return ''

  @classmethod
  def store(cls, institution, session_name, students_data):
    students = Students(data = students_data)
    students.key = Students.students_key(institution, session_name)
    students.put()


class Requirements(ndb.Model):
  """Examples: 8th Core, PE"""
  data = ndb.StringProperty()

  @classmethod
  def requirements_key(cls, institution, session):
    return ndb.Key("InstitutionKey", institution,
                   Session, session,
                   Requirements, "requirements")

  @classmethod
  def fetch(cls, institution, session):
    requirements = Requirements.requirements_key(institution, session).get()
    if requirements:
      return requirements.data
    else:
      return ''

  @classmethod
  def store(cls, institution, session_name, requirements_data):
    requirements = Requirements(data = requirements_data)
    requirements.key = Requirements.requirements_key(institution, session_name)
    requirements.put()
