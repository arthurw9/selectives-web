import logging
import yaml
import time
import webapp2
try:
  from google.appengine.ext import ndb
except:
  logging.info("google.appengine.ext not found. "
                "We must be running in a unit test.")
  import fake_ndb
  ndb = fake_ndb.FakeNdb()


GLOBAL_KEY = ndb.Key("global", "global")


# TODO: make all methods camel case with initial caps
# TODO: Fetch methods should come in predictable flavors:
# - Plain Fetch returns a string
# - FetchAll returns a list of strings
# - FetchEntity returns a ndbModel object
# - FetchAllEntities returns a list of ndbModel object

class Timer(object):

  def __init__(self):
    self.start_time = time.time()
    self.events = []
    self.addEvent('start')

  def getTime(self):
    return time.time() - self.start_time

  def startEvent(self, *entry):
    event = [self.getTime(), 0]
    event.extend(entry)
    self.events.append(event)
    return len(self.events) - 1

  def finishEvent(self, idx):
    duration = self.getTime() - self.events[idx][0]
    self.events[idx][1] = duration

  def addEvent(self, name):
    _ = self.startEvent(name)

  @classmethod
  def startTiming(cls):
    logging.error("starting timer")
    req = webapp2.get_request()
    req.registry['timer'] = Timer()

  @classmethod
  def getDataStr(cls):
    req = webapp2.get_request();
    timer = req.registry['timer']
    timer.addEvent('done')
    result = ["Timer:\n\nCurr request = " + str(req)]
    result.append("\ntiming: ")
    for e in timer.events:
      result.append("%0.3f, %0.3f, %s" % (e[0], e[1], str(e[2:])))
    result.append("\n");
    return '\n'.join(result)


def timed(fn):
  def wrapper(*argv, **kwargs):
    req = webapp2.get_request()
    if 'timer' in req.registry:
      timer =  req.registry['timer']
      class_name = str(argv[0]).partition("<")[0]
      event_idx = timer.startEvent(class_name, fn.__name__, argv[1:])
    ret_value = fn(*argv, **kwargs)
    if 'timer' in req.registry:
      timer.finishEvent(event_idx)
    return ret_value
  return wrapper


class GlobalAdmin(ndb.Model):
  """email addresses for users with full access to the site."""
  email = ndb.StringProperty()

  @classmethod
  @timed
  def global_admin_key(cls, email):
    return ndb.Key("global", "global", GlobalAdmin, email);

  @classmethod
  @timed
  def Store(cls, email_addr):
    admin = GlobalAdmin(email=email_addr)
    admin.key = GlobalAdmin.global_admin_key(email_addr)
    admin.put();

  @classmethod
  @timed
  def Delete(cls, email_addr):
    GlobalAdmin.global_admin_key(email_addr).delete()

  @classmethod
  @timed
  def FetchAll(cls):
    return [ a.email for a in GlobalAdmin.query(ancestor=GLOBAL_KEY).fetch() ]


class Admin(ndb.Model):
  """email addresses for users with full access to an institution."""
  email = ndb.StringProperty()

  @classmethod
  @timed
  def admin_key_partial(cls, institution):
    return ndb.Key('InstitutionKey', institution);

  @classmethod
  @timed
  def admin_key(cls, institution, email):
    return ndb.Key('InstitutionKey', institution, Admin, email);

  @classmethod
  @timed
  def Store(cls, institution, email_addr):
    key = Admin.admin_key(institution, email_addr)
    Admin(email=email_addr, key=key).put();

  @classmethod
  @timed
  def Delete(cls, institution, email_addr):
    Admin.admin_key(institution, email_addr).delete()

  @classmethod
  @timed
  def FetchAll(cls, institution):
    admins = Admin.query(ancestor=Admin.admin_key_partial(institution)).fetch()
    return [ a.email for a in admins ]

  @classmethod
  @timed
  def GetInstitutionNames(cls, email):
    """returns False or a list of institution names."""
    admin_list = Admin.query(Admin.email == email).fetch()
    if admin_list == None:
      return []
    elif len(admin_list) <= 0:
      return []
    else:
      return [ admin.key.parent().id() for admin in admin_list ]


class Institution(ndb.Model):
  """Institution name"""
  name = ndb.StringProperty()

  @classmethod
  @timed
  def institution_key(cls, name):
    return ndb.Key("global", "global", Institution, name)

  @classmethod
  @timed
  def store(cls, name):
    Institution(name=name, key=Institution.institution_key(name)).put()

  @classmethod
  @timed
  def FetchAllInstitutions(cls):
    return Institution.query(ancestor=GLOBAL_KEY).fetch()


class Session(ndb.Model):
  """Session name"""
  name = ndb.StringProperty()

  @classmethod
  @timed
  def session_key_partial(cls, institution):
    return ndb.Key("InstitutionKey", institution)

  @classmethod
  @timed
  def session_key(cls, institution, session_name):
    return ndb.Key(Session, session_name,
                   parent=ndb.Key("InstitutionKey", institution))

  @classmethod
  @timed
  def FetchAllSessions(cls, institution):
    return Session.query(
        ancestor=Session.session_key_partial(institution)).fetch()

  @classmethod
  @timed
  def store(cls, institution, session_name):
    session = Session(name=session_name)
    session.key = Session.session_key(institution, session_name)
    session.put()

  @classmethod
  @timed
  def delete(cls, institution, session_name):
    Session.session_key(institution, session_name).delete()


class ServingSession(ndb.Model):
  """Which session is currently serving. Empty if none."""
  session_name = ndb.StringProperty()
  login_type = ndb.StringProperty(choices=['verification', 'preferences', 'schedule', 'preregistration', 'postregistration'])

  @classmethod
  @timed
  def serving_session_key(cls, institution):
    return ndb.Key("InstitutionKey", institution, ServingSession, "serving_session")

  @classmethod
  @timed
  def FetchEntity(cls, institution):
    ss = ServingSession.serving_session_key(institution).get()
    if ss:
      return ss
    ss = ServingSession()
    ss.key = ServingSession.serving_session_key(institution)
    return ss

  @classmethod
  @timed
  def store(cls, institution, session_name, login_type):
    serving_session = ServingSession()
    serving_session.session_name = session_name
    serving_session.login_type = login_type
    serving_session.key = ServingSession.serving_session_key(institution)
    serving_session.put()

  @classmethod
  @timed
  def delete(cls, institution):
    ServingSession.serving_session_key(institution).delete()

  @classmethod
  @timed
  def FetchAllEntities(cls):
    """Returns a list of triples (institution_name, session_name, login_type)"""
    serving_sessions = ServingSession.query().fetch()
    for ss in serving_sessions:
      ss.institution_name = ss.key.parent().id()
    return serving_sessions


class Dayparts(ndb.Model):
  """Examples: Monday AM, or M-W-F 8am-9am"""
  data = ndb.TextProperty()
  jdata = ndb.JsonProperty()

  @classmethod
  @timed
  def dayparts_key(cls, institution, session):
    return ndb.Key("InstitutionKey", institution,
                   Session, session,
                   Dayparts, "dayparts")

  @classmethod
  @timed
  def FetchJson(cls, institution, session):
    dayparts = Dayparts.dayparts_key(institution, session).get()
    if dayparts:
      return dayparts.jdata
    else:
      return ''

  @classmethod
  @timed
  def Fetch(cls, institution, session):
    dayparts = Dayparts.dayparts_key(institution, session).get()
    if dayparts:
      return dayparts.data
    else:
      return ''

  @classmethod
  @timed
  def store(cls, institution, session_name, dayparts_data):
    dayparts = Dayparts(data = dayparts_data,
                        jdata = yaml.load(dayparts_data))
    dayparts.key = Dayparts.dayparts_key(institution, session_name)
    dayparts.put()


class Classes(ndb.Model):
  """List of classes in yaml and json format."""
  data = ndb.TextProperty()
  jdata = ndb.JsonProperty()

  @classmethod
  @timed
  def classes_key(cls, institution, session):
    return ndb.Key("InstitutionKey", institution,
                   Session, session,
                   Classes, "classes")

  @classmethod
  @timed
  def FetchJson(cls, institution, session):
    classes = Classes.classes_key(institution, session).get()
    if classes:
      return classes.jdata
    else:
      return ''

  @classmethod
  @timed
  def Fetch(cls, institution, session):
    classes = Classes.classes_key(institution, session).get()
    if classes:
      return classes.data
    else:
      return ''

  @classmethod
  @timed
  def store(cls, institution, session_name, classes_data):
    classes = Classes(data = classes_data,
                      jdata = yaml.load(classes_data))
    classes.key = Classes.classes_key(institution, session_name)
    classes.put()


class Students(ndb.Model):
  """List of students in yaml and json format."""
  data = ndb.TextProperty()
  jdata = ndb.JsonProperty()

  @classmethod
  @timed
  def students_key(cls, institution, session):
    return ndb.Key("InstitutionKey", institution,
                   Session, session,
                   Students, "students")

  @classmethod
  @timed
  def FetchJson(cls, institution, session):
    students = Students.students_key(institution, session).get()
    if students:
      return students.jdata
    else:
      return ''

  @classmethod
  @timed
  def Fetch(cls, institution, session):
    students = Students.students_key(institution, session).get()
    if students:
      return students.data
    else:
      return ''

  @classmethod
  @timed
  def store(cls, institution, session_name, students_data):
    students = Students(data = students_data,
                        jdata = yaml.load(students_data))
    students.key = Students.students_key(institution, session_name)
    students.put()


class Requirements(ndb.Model):
  """Examples: 8th Core, PE"""
  data = ndb.TextProperty()
  jdata = ndb.JsonProperty()

  @classmethod
  @timed
  def requirements_key(cls, institution, session):
    return ndb.Key("InstitutionKey", institution,
                   Session, session,
                   Requirements, "requirements")

  @classmethod
  @timed
  def FetchJson(cls, institution, session):
    requirements = Requirements.requirements_key(institution, session).get()
    if requirements:
      return requirements.jdata
    else:
      return ''

  @classmethod
  @timed
  def Fetch(cls, institution, session):
    requirements = Requirements.requirements_key(institution, session).get()
    if requirements:
      return requirements.data
    else:
      return ''

  @classmethod
  @timed
  def store(cls, institution, session_name, requirements_data):
    requirements = Requirements(
        data = requirements_data,
        jdata = yaml.load(requirements_data))
    requirements.key = Requirements.requirements_key(institution, session_name)
    requirements.put()


class GroupsClasses(ndb.Model):
  """List of class groups in yaml and json format."""
  data = ndb.TextProperty()
  jdata = ndb.JsonProperty()

  @classmethod
  @timed
  def groups_classes_key(cls, institution, session):
    return ndb.Key("InstitutionKey", institution,
                   Session, session,
                   GroupsClasses, "groups_classes")

  @classmethod
  @timed
  def FetchJson(cls, institution, session):
    groups_classes = GroupsClasses.groups_classes_key(institution, session).get()
    if groups_classes:
      return groups_classes.jdata
    else:
      return ''

  @classmethod
  @timed
  def Fetch(cls, institution, session):
    groups_classes = GroupsClasses.groups_classes_key(institution, session).get()
    if groups_classes:
      return groups_classes.data
    else:
      return ''

  @classmethod
  @timed
  def store(cls, institution, session_name, groups_classes_data):
    groups_classes = GroupsClasses(
        data = groups_classes_data,
        jdata = yaml.load(groups_classes_data))
    groups_classes.key = GroupsClasses.groups_classes_key(institution, session_name)
    groups_classes.put()

class GroupsStudents(ndb.Model):
  """List of student groups in yaml and json format."""
  data = ndb.TextProperty()
  jdata = ndb.JsonProperty()

  @classmethod
  @timed
  def groups_students_key(cls, institution, session):
    return ndb.Key("InstitutionKey", institution,
                   Session, session,
                   GroupsStudents, "groups_students")

  @classmethod
  @timed
  def FetchJson(cls, institution, session):
    groups_students = GroupsStudents.groups_students_key(institution, session).get()
    if groups_students:
      return groups_students.jdata
    else:
      return ''

  @classmethod
  @timed
  def Fetch(cls, institution, session):
    groups_students = GroupsStudents.groups_students_key(institution, session).get()
    if groups_students:
      return groups_students.data
    else:
      return ''

  @classmethod
  @timed
  def store(cls, institution, session_name, groups_students_data):
    groups_students = GroupsStudents(
        data = groups_students_data,
        jdata = yaml.load(groups_students_data))
    groups_students.key = GroupsStudents.groups_students_key(institution, session_name)
    groups_students.put()


class RecentAccess(ndb.Model):
  date_time = ndb.DateTimeProperty(auto_now=True)

  @classmethod
  @timed
  def recent_access_key(cls, email_str):
    return ndb.Key(RecentAccess, email_str)

  @classmethod
  @timed
  def Store(cls, email_str):
    recent_access = RecentAccess()
    recent_access.key = RecentAccess.recent_access_key(email_str)
    recent_access.put()

  @classmethod
  @timed
  def FetchRecentAccess(cls):
    recent = RecentAccess.query().order(-RecentAccess.date_time).fetch(20)
    return [ (a.key.id(), str(a.date_time)) for a in recent ] 


class Preferences(ndb.Model):
  # Note: Email is not set in the DB Entity because it is part of the key. 
  # It is added to the object after it is fetched.
  # TODO: Can email be deleted?
  email = ndb.StringProperty()
  want = ndb.StringProperty()
  dontcare = ndb.StringProperty()
  dontwant = ndb.StringProperty()

  @classmethod
  @timed
  def preferences_key(cls, email, institution, session):
    return ndb.Key("InstitutionKey", institution,
                   Session, session,
                   Preferences, email)

  @classmethod
  @timed
  def Store(cls, email, institution, session, want, dontcare, dontwant):
    """params want, dontcare, and dontwant are lists of ints"""
    prefs = Preferences()
    prefs.key = Preferences.preferences_key(email, institution, session)
    if set(want).intersection(dontcare):
      raise Exception("some classes are in both want and dontcare." +
                      "\nwant: " + ','.join(want) + 
                      "\ndontcare: " + ','.join(dontcare) +
                      "\ndontwant: " + ','.join(dontwant))
    if set(dontcare).intersection(dontwant):
      raise Exception("some classes are in both dontcare and dontwant" +
                      "\nwant: " + ','.join(want) + 
                      "\ndontcare: " + ','.join(dontcare) +
                      "\ndontwant: " + ','.join(dontwant))
    if set(want).intersection(dontwant):
      raise Exception("some classes are in both want and dontwant" +
                      "\nwant: " + ','.join(want) + 
                      "\ndontcare: " + ','.join(dontcare) +
                      "\ndontwant: " + ','.join(dontwant))
    prefs.want = ','.join(want)
    prefs.dontcare = ','.join(dontcare)
    prefs.dontwant = ','.join(dontwant)
    logging.info('saving want = %s' % prefs.want)
    logging.info('saving dontwant = %s' % prefs.dontwant)
    logging.info('saving dontcare = %s' % prefs.dontcare)
    prefs.put()

  @classmethod
  @timed
  def FetchEntity(cls, email, institution, session):
    prefs = Preferences.preferences_key(email, institution, session).get()
    if not prefs:
      prefs = Preferences()
      prefs.email = email
      prefs.want = ""
      prefs.dontcare = ""
      prefs.dontwant = ""
    return prefs


class Schedule(ndb.Model):
  class_ids = ndb.StringProperty()

  @classmethod
  @timed
  def schedule_key(cls, institution, session, email):
    return ndb.Key("InstitutionKey", institution,
                   Session, session,
                   Schedule, email)

  @classmethod
  @timed
  def Store(cls, institution, session, email, class_ids):
    schedule = Schedule()
    schedule.key = Schedule.schedule_key(institution, session, email)
    schedule.class_ids = class_ids
    schedule.put()

  @classmethod
  @timed
  def Fetch(cls, institution, session, email):
    schedule = Schedule.schedule_key(institution, session, email).get()
    if not schedule:
      return ""
    else:
      return schedule.class_ids


class ClassRoster(ndb.Model):
  # comma separated list of student emails
  student_emails = ndb.TextProperty()
  # class obj, yaml.dump and yaml.load takes too long
  jclass_obj = ndb.JsonProperty()

  @classmethod
  @timed
  def class_roster_key(cls, institution, session, class_id):
    class_id = str(class_id)
    return ndb.Key("InstitutionKey", institution,
                   Session, session,
                   ClassRoster, class_id)

  @classmethod
  @timed
  def Store(cls, institution, session, class_obj, student_emails):
    student_emails = student_emails.strip()
    if len(student_emails) and student_emails[-1] == ',':
      student_emails = student_emails[:-1]
    class_id = str(class_obj['id'])
    roster = ClassRoster()
    roster.key = ClassRoster.class_roster_key(institution, session, class_id)
    roster.student_emails = student_emails
    roster.jclass_obj = class_obj
    roster.put()

  @classmethod
  @timed
  def FetchEntity(cls, institution, session, class_id):
    class_id = str(class_id)
    roster = ClassRoster.class_roster_key(institution, session, class_id).get()
    if roster:
      c = roster.jclass_obj
      r = {}
      r['emails'] = roster.student_emails.split(",")
      if r['emails'][0] == "":
        r['emails'] = r['emails'][1:]
      r['class_name'] = c['name']
      r['class_id'] = c['id']
      r['class_details'] = roster.jclass_obj
      r['max_enrollment'] = c['max_enrollment']
      r['remaining_space'] = c['max_enrollment'] - len(r['emails'])
      return r
    logging.info("Class Roster NOT found: [%s] [%s] [%s]" % (
          institution, session, class_id))
    r = {}
    r['emails'] = []
    r['class_id'] = 0
    r['class_name'] = 'None'
    r['class_details'] = ''
    r['max_enrollment'] = 0
    r['remaining_space'] = 0
    return r


class ErrorCheck(ndb.Model):
  data = ndb.StringProperty(choices=['OK', 'FAIL', 'UNKNOWN'])

  @classmethod
  @timed
  def errorcheck_key(cls, institution, session):
    return ndb.Key("InstitutionKey", institution,
                   Session, session,
                   ErrorCheck, "errorcheck")

  @classmethod
  @timed
  def Fetch(cls, institution, session):
    errorcheck = ErrorCheck.errorcheck_key(institution, session).get()
    if errorcheck:
      return errorcheck.data
    else:
      return 'UNKNOWN'

  @classmethod
  @timed
  def Store(cls, institution, session_name, errorcheck_data):
    errorcheck = ErrorCheck(data = errorcheck_data)
    errorcheck.key = ErrorCheck.errorcheck_key(institution, session_name)
    errorcheck.put()


class DBVersion(ndb.Model):
  data = ndb.IntegerProperty()

  @classmethod
  @timed
  def db_version_key(cls, institution, session):
    return ndb.Key("InstitutionKey", institution,
                   Session, session,
                   DBVersion, "db_version")
  @classmethod
  @timed
  def Fetch(cls, institution, session):
    db_version = DBVersion.db_version_key(institution, session).get()
    if db_version:
      return db_version.data
    else:
      return 0

  @classmethod
  @timed
  def Store(cls, institution, session, version):
    db_version = DBVersion(data = version)
    db_version.key = DBVersion.db_version_key(institution, session)
    db_version.put()
