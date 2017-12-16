import logging
import yaml
import time
import webapp2
import datetime
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

class ServingRules(ndb.Model):
  """List of serving rules in yaml and json format."""
  data = ndb.TextProperty()
  jdata = ndb.JsonProperty()

  @classmethod
  @timed
  def serving_rules_key(cls, institution, session):
    return ndb.Key("InstitutionKey", institution,
                   Session, session,
                   ServingRules, "serving_rules")

  @classmethod
  @timed
  def FetchJson(cls, institution, session):
    serving_rules = ServingRules.serving_rules_key(institution, session).get()
    if serving_rules:
      return serving_rules.jdata
    else:
      return ''

  @classmethod
  @timed
  def Fetch(cls, institution, session):
    serving_rules = ServingRules.serving_rules_key(institution, session).get()
    if serving_rules:
      return serving_rules.data
    else:
      return ''

  @classmethod
  @timed
  def store(cls, institution, session_name, sr_data):
    serving_rules = ServingRules(data = sr_data,
                                 jdata = yaml.load(sr_data))
    serving_rules.key = ServingRules.serving_rules_key(institution, session_name)
    serving_rules.put()


class ServingSession(ndb.Model):
  """Which session is currently serving. Empty if none."""
  session_name = ndb.StringProperty()
  start_page = ndb.StringProperty(choices=['verification', 'preferences', 'schedule', 'preregistration', 'postregistration'])

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
  def store(cls, institution, session_name, start_page):
    serving_session = ServingSession()
    serving_session.session_name = session_name
    serving_session.start_page = start_page
    serving_session.key = ServingSession.serving_session_key(institution)
    serving_session.put()

  @classmethod
  @timed
  def delete(cls, institution):
    ServingSession.serving_session_key(institution).delete()

  @classmethod
  @timed
  def FetchAllEntities(cls):
    """Returns a list of triples (institution_name, session_name, start_page)"""
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


class Teachers(ndb.Model):
  """List of teachers in yaml and json format."""
  data = ndb.TextProperty()
  jdata = ndb.JsonProperty()

  @classmethod
  @timed
  def teachers_key(cls, institution, session):
    return ndb.Key("InstitutionKey", institution,
                   Session, session,
                   Teachers, "teachers")

  @classmethod
  @timed
  def FetchJson(cls, institution, session):
    teachers = Teachers.teachers_key(institution, session).get()
    if teachers:
      return teachers.jdata
    else:
      return ''

  @classmethod
  @timed
  def Fetch(cls, institution, session):
    teachers = Teachers.teachers_key(institution, session).get()
    if teachers:
      return teachers.data
    else:
      return ''

  @classmethod
  @timed
  def store(cls, institution, session_name, teachers_data):
    teachers = Teachers(data = teachers_data,
                        jdata = yaml.load(teachers_data))
    teachers.key = Teachers.teachers_key(institution, session_name)
    teachers.put()


class AutoRegister(ndb.Model):
  """Examples: 8th Core, 7th Core, 6th Core"""
  data = ndb.TextProperty()
  jdata = ndb.JsonProperty()

  @classmethod
  @timed
  def auto_register_key(cls, institution, session):
    return ndb.Key("InstitutionKey", institution,
                   Session, session,
                   AutoRegister, "auto_register")

  @classmethod
  @timed
  def FetchJson(cls, institution, session):
    auto_register = AutoRegister.auto_register_key(institution, session).get()
    if auto_register:
      return auto_register.jdata
    else:
      return ''

  @classmethod
  @timed
  def Fetch(cls, institution, session):
    auto_register = AutoRegister.auto_register_key(institution, session).get()
    if auto_register:
      return auto_register.data
    else:
      return ''

  @classmethod
  @timed
  def store(cls, institution, session_name, auto_register_data):
    auto_register = AutoRegister(
        data = auto_register_data,
        jdata = yaml.load(auto_register_data))
    auto_register.key = AutoRegister.auto_register_key(institution, session_name)
    auto_register.put()


class Requirements(ndb.Model):
  """Examples: one PE required, PEs must be on opposite sides of the week"""
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
  last_modified = ndb.DateTimeProperty() # See note below.

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
    # Appengine datetimes are stored in UTC, so by around 4pm the date is wrong.
    # This kludge gets PST, but it doesn't handle daylight savings time,
    # but off by one hour is better than off by eight hours. The date will
    # be wrong half the year when someone is modifying data between
    # 11pm and midnight.
    schedule.last_modified = datetime.datetime.now() - datetime.timedelta(hours=8)
    schedule.put()

  @classmethod
  @timed
  def Fetch(cls, institution, session, email):
    schedule = Schedule.schedule_key(institution, session, email).get()
    if not schedule:
      return ""
    else:
      schedule.class_ids = schedule.class_ids.strip(',').strip()
      return schedule.class_ids

  @classmethod
  @timed
  def FetchEntity(cls, institution, session, email):
    schedule = Schedule.schedule_key(institution, session, email).get()
    if not schedule:
      return {}
    else:
      schedule.class_ids = schedule.class_ids.strip(',').strip()
      return schedule


class ClassRoster(ndb.Model):
  # comma separated list of student emails
  student_emails = ndb.TextProperty()
  # class obj, yaml.dump and yaml.load takes too long
  jclass_obj = ndb.JsonProperty()
  # Not using auto_now=True on purpose, see note below.
  last_modified = ndb.DateTimeProperty()

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
    # Appengine datetimes are stored in UTC, so by around 4pm the date is wrong.
    # This is a kludgy way to get PST. It doesn't handle daylight savings time,
    # but off by one hour is better than off by eight.
    # The alternatives:
    #  - pytz has a few hundred files.
    #  - tzinfo has four methods to implement which I don't need.
    # Don't use hour because it will be wrong half the year.
    # If someone wants to do this the "right" way later, that would be fine.
    roster.last_modified = datetime.datetime.now() - datetime.timedelta(hours=8)
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
      if 'instructor' in c:
        r['instructor'] = c['instructor']
      r['schedule'] = c['schedule']
      r['class_details'] = roster.jclass_obj
      r['max_enrollment'] = c['max_enrollment']
      r['remaining_space'] = c['max_enrollment'] - len(r['emails'])
      if (roster.last_modified):
        r['last_modified'] = roster.last_modified
      else:
        r['last_modified'] = None
      return r
    logging.info("Class Roster NOT found: [%s] [%s] [%s]" % (
          institution, session, class_id))
    r = {}
    r['emails'] = []
    r['class_id'] = 0
    r['class_name'] = 'None'
    r['schedule'] = {}
    r['class_details'] = ''
    r['max_enrollment'] = 0
    r['remaining_space'] = 0
    r['last_modified'] = None
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

class Attendance(ndb.Model):
  jdata = ndb.JsonProperty()

  # 'c_id' is a class id.
  # 'jdata' is a dictionary:
  # {date1: {'absent': [email1, email2, ...],
  #          'present': [email1, email2, ...]},
  #  date2: {'absent': [email1, email2, ...],
  #          'present': [email1, email2, ...]},
  #  ...}
  @classmethod
  def attendance_key(cls, institution, session, c_id):
    return ndb.Key("InstitutionKey", institution,
                   Session, session,
                   'Attendance', c_id)

  @classmethod
  def FetchJson(cls, institution, session, c_id):
    attendance = Attendance.attendance_key(institution, session, c_id).get()
    if attendance:
      return attendance.jdata
    else:
      return {}

  @classmethod
  def store(cls, institution, session_name, c_id, attendance_obj):
    attendance = Attendance(jdata = attendance_obj)
    attendance.key = Attendance.attendance_key(institution, session_name, c_id)
    attendance.put()
