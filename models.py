from google.appengine.ext import ndb

GLOBAL_KEY = ndb.Key("global", "global")


def global_admin_key(email):
  return ndb.Key("global", "global", Admin, email);


def admin_key_partial(institution):
  return ndb.Key('InstitutionKey', institution);


def admin_key(institution, email):
  return ndb.Key('InstitutionKey', institution, Admin, email);


class Admin(ndb.Model):
  """Administrator email address."""
  email = ndb.StringProperty()

  @classmethod
  def storeInstitutionAdmin(cls, institution, email_addr):
    key = admin_key(institution, email_addr)
    Admin(email=email_addr, key=key).put();

  @classmethod
  def deleteInstitutionAdmin(cls, institution, email_addr):
    admin_key(institution, email_addr).delete()

  @classmethod
  def store(cls, email_addr):
    key = global_admin_key(email_addr)
    Admin(email=email_addr, key=key).put();

  @classmethod
  def delete(cls, email_addr):
    global_admin_key(email_addr).delete()

  @classmethod
  def FetchAllGlobalAdmins(cls):
    return Admin.query(ancestor=GLOBAL_KEY).fetch()

  @classmethod
  def FetchAllInstitutionAdmins(cls, institution):
    return Admin.query(ancestor=admin_key_partial(institution)).fetch()


def institution_key(name):
  return ndb.Key("global", "global", Institution, name)


class Institution(ndb.Model):
  """Institution name"""
  name = ndb.StringProperty()

  @classmethod
  def store(cls, name):
      Institution(name=name, key=institution_key(name)).put()

  @classmethod
  def FetchAllInstitutions(cls):
    return Institution.query(ancestor=GLOBAL_KEY).fetch()


def session_key_partial(institution):
  return ndb.Key("InstitutionKey", institution)

def session_key(institution, session_name):
  return ndb.Key(Session, session_name,
                 parent=ndb.Key("InstitutionKey", institution))


class Session(ndb.Model):
  """Session name"""
  name = ndb.StringProperty()

  @classmethod
  def FetchAllSessions(cls, institution):
    return Session.query(
        ancestor=session_key_partial(institution)).fetch()

  @classmethod
  def store(cls, institution, session_name):
    session = Session(name=session_name)
    session.key = session_key(institution, session_name) 
    session.put()

  @classmethod
  def delete(cls, institution, session_name):
    session_key(institution, session_name).delete()


def serving_session_key(institution):
  return ndb.Key("InstitutionKey", institution, ServingSession, "serving_session")


class ServingSession(ndb.Model):
  """Which session is currently serving. Empty if none."""
  session_name = ndb.StringProperty()
  login_type = ndb.StringProperty()

  @classmethod
  def fetch(cls, institution):
    ss = serving_session_key(institution).get()
    if ss:
      return ss
    ss = ServingSession()
    ss.key = serving_session_key(institution)
    return ss

  @classmethod
  def store(cls, institution, session_name, login_type):
    serving_session = ServingSession()
    serving_session.session_name = session_name
    serving_session.login_type = login_type
    serving_session.key = serving_session_key(institution)
    serving_session.put()

  @classmethod
  def delete(cls, institution):
    serving_session_key(institution).delete()


def dayparts_key(institution, session):
  return ndb.Key("InstitutionKey", institution,
                 Session, session,
                 Dayparts, "dayparts")


class Dayparts(ndb.Model):
  """Examples: Monday AM, or M-W-F 8am-9am"""
  data = ndb.StringProperty()

  @classmethod
  def fetch(cls, institution, session):
    dayparts = dayparts_key(institution, session).get()
    if dayparts:
      return dayparts.data
    else:
      return ''

  @classmethod
  def store(cls, institution, session_name, dayparts_data):
    dayparts = Dayparts(data = dayparts_data)
    dayparts.key = dayparts_key(institution, session_name)
    dayparts.put()


def classes_key(institution, session):
  return ndb.Key("InstitutionKey", institution,
                 Session, session,
                 Classes, "classes")


class Classes(ndb.Model):
  """List of classes in yaml format."""
  data = ndb.StringProperty()

  @classmethod
  def fetch(cls, institution, session):
    classes = classes_key(institution, session).get()
    if classes:
      return classes.data
    else:
      return ''

  @classmethod
  def store(cls, institution, session_name, classes_data):
    classes = Classes(data = classes_data)
    classes.key = classes_key(institution, session_name)
    classes.put()


def students_key(institution, session):
  return ndb.Key("InstitutionKey", institution,
                 Session, session,
                 Students, "students")


class Students(ndb.Model):
  """List of students in yaml format."""
  data = ndb.StringProperty()

  @classmethod
  def fetch(cls, institution, session):
    students = students_key(institution, session).get()
    if students:
      return students.data
    else:
      return ''

  @classmethod
  def store(cls, institution, session_name, students_data):
    students = Students(data = students_data)
    students.key = students_key(institution, session_name)
    students.put()
