from google.appengine.ext import ndb

GLOBAL_KEY = ndb.Key("global", "global")

def global_admin_key(email):
  return ndb.Key("global", "global", Admin, email);

def admin_key(institution, email):
  return ndb.Key("Institution", institution, Admin, email);

class Admin(ndb.Model):
  """Administrator email address."""
  email = ndb.StringProperty()

  @classmethod
  def store(cls, institution, email_addr):
    key = admin_key(institution, email_addr)
    Admin(email=email_addr, key=key).put();

  @classmethod
  def delete(cls, institution, email_addr):
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
