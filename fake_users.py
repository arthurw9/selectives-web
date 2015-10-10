
class FakeUsers(object):

  def __init__(self, email):
    self.current_user_email = email

  def get_current_user(self):
    return self

  def email(self):
    return self.current_user_email
