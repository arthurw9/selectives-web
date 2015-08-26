from google.appengine.api import users

# TODO: figure out what the user has access to and take them there.

class Authorizer(object):

  def __init__(self):
    self.user = users.get_current_user()
    self.destination = None

  def ShouldRedirect(self, handler):
    if not self.user:
      self.destination = users.create_login_url(handler.request.uri)
      return True
    return False

  def Redirect(self, handler):
    if self.destination:
      handler.redirect(self.destination)

  def GetLogoutUrl(self, handler):
    return users.create_logout_url(handler.request.uri)
