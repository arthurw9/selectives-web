import datetime


class FakeNdb(object):

  def __init__(self, *args, **kwargs):
    self.Model = FakeNdb
    self.Model.stored_data = []
    self.init_args = args
    self.init_kwargs = kwargs

  def Key(self, *args, **kwargs):
    return args

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
    if 'key' in self.__dict__:
      return self.key

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