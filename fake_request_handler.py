

class RequestHandler(object):

  def __init__(self, param_dict={}):
    self.param_dict = param_dict
    self.request = self

  def SetPath(self, path):
    self.request.path = path

  def get(self, key):
    return self.param_dict[key]