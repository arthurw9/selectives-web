import datetime
import yaml
import logging

class FakeNdb(object):

  class transactional(object):
    def __init__(self, retries, xg):
      self.retries = retries
      self.xg = xg
 
    def __call__(self, func):
      # called at decoration time
      def transaction(*args, **kw_args):
        return func(*args, **kw_args)
      return transaction

  def __init__(self, *args, **kwargs):
    self.Model = FakeNdb
    self.Model.stored_data = []
    self.init_args = args
    self.init_kwargs = kwargs

  def Key(self, *args, **kwargs):
    k = FakeNdb()
    k.key = args
    return k

  def StringProperty(self):
    return "StringProperty"

  def TextProperty(self):
    return "TextProperty"

  def DateTimeProperty(self):
    return "DateTimeProperty"

  def DateTimeProperty(self, **kwargs):
    return datetime.datetime.now()

  def put(self, *args, **kwargs):
    self.Model.stored_data.append(self)

  def GetKey(self):
    while 'key' in self.__dict__ and isinstance(self.key, FakeNdb):
      self = self.key
    if 'key' in self.__dict__:
      return self.key
    else:
      raise Exception("no key")

  def GetProperty(self, name):
    if name in self.__dict__:
      return self.__dict__[name]


class FakeGlobalAdmin(object):
  
  def __init__(self, email_list):
    self.email_list = email_list

  def FetchAll(self):
    return self.email_list


class FakeStudents(object):

  def __init__(self, students):
    self.students = students

  def fetch(self, institution, session):
    return self.students


class FakeAdmin(object):

  def __init__(self, email_list):
    self.email_list = email_list

  def FetchAll(self, institution):
    return self.email_list


class FakeServingSession(object):

  def __init__(self, institution, session, login_type):
    self.institution = institution
    self.session_name = session
    self.login_type = login_type

  def FetchEntity(self, institution):
    return self


class FakeClasses(object):

  def __init__(self, class_data):
    self.class_data = yaml.dump(class_data)

  def Fetch(self, institution, session):
    return self.class_data


class FakeSchedule(object):

  def __init__(self):
    self.data = {}

  def Key(self, institution, session, email):
    return "%s,%s,%s" % (institution, session, email)

  def Store(self, institution, session, email, class_ids):
    self.data[self.Key(institution, session, email)] = class_ids

  def Fetch(self, institution, session, email):
    key = self.Key(institution, session, email)
    if key in self.data:
      return self.data[key]
    return ""


class FakeClassRoster(object):

  def __init__(self):
    self.data = {}

  def Key(self, institution, session, class_id):
    return "%s,%s,%s" % (institution, session, class_id)

  def Store(self, institution, session, class_obj, emails):
    class_id = str(class_obj['id'])
    self.data[self.Key(institution, session, class_id)] = (class_obj, emails)

  def FetchEntity(self, institution, session, class_id):
    key = self.Key(institution, session, class_id)
    if key in self.data:
      (class_obj, emails) = self.data[key]
      c = class_obj
      r = {}
      r['emails'] = emails.split(",")
      r['class_name'] = c['name']
      r['class_id'] = c['id']
      r['class_details'] = class_obj
      r['max_enrollment'] = c['max_enrollment']
      r['remaining_space'] = c['max_enrollment'] - len(r['emails'])
      logging.info("Class Roster found: [%s] [%s] [%s]" % (
          institution, session, class_id))
      logging.info("class [%s] emails: %s" % (
          c['id'], emails))
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

class FakeGroupsStudents(object):

  def __init__(self, student_group_data):
    self.data = yaml.dump(student_group_data)

  def fetch(self, institution, session):
    return self.data
