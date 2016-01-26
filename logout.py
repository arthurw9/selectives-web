# http://ptspts.blogspot.ca/2011/12/how-to-log-out-from-appengine-app-only.html

import Cookie
import os
from google.appengine.api import users
import webapp2
import logging
import authorizer

class LogoutPage(webapp2.RequestHandler):
  def get(self):
    if os.environ.get('SERVER_SOFTWARE', '').startswith('Development/'):
      self.redirect(users.create_logout_url('/'))
      return

    # On the production instance, we just remove the session cookie, because
    # redirecting users.create_logout_url(...) would log out of all Google
    # (e.g. Gmail, Google Calendar).
    #
    # It seems AppEngine is setting the ACSID cookie for http://
    # and the SACSID cookie for https:// . We unset both.
    cookie = Cookie.SimpleCookie()
    cookie['ACSID'] = ''
    cookie['ACSID']['expires'] = -86400 # In the past, a day ago
    self.response.headers.add_header(*cookie.output().split(': ', 1))
    cookie = Cookie.SimpleCookie()
    cookie['SACSID'] = ''
    cookie['SACSID']['expires'] = -86400 # In the past, a day ago
    self.response.headers.add_header(*cookie.output().split(': ', 1))

    auth = authorizer.Authorizer(self)
    auth.Redirect()