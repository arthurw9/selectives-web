"""YAYV = Yet Another Yaml Validator

Use this module to validate that input yaml meets your requirements.
Exceptions are only raised if there is a problem with the schema.
Problems with the input YAML will just return False and more info in
the error message.
"""
import yaml
import testbase
import traceback

class ByExample(object):
  """for validating yaml by example.

     This class can be used for simple schemas with no self reference.
     Inialize with an example where all lists have just one element and all
     leaves are one of the following keywords: 
     OPTIONAL, REQUIRED, UNIQUE, AUTO_INC
  """

  def __init__(self, schema):
    """The schema is basically an example of valid input."""
    self.schema = yaml.load(schema)

  def ErrorMessage(self):
    return '\n'.join(self.error_message)

  def IsValid(self, yaml_str):
    self.unique_values = {}
    self.counters = {}
    self.error_message = []
    try:
      self.yaml_obj = yaml.load(yaml_str)
    except:
      self._AddError("ROOT", traceback.print_exc())
      return False
    return self._Validate(self.schema, self.yaml_obj, "ROOT")

  def _AddError(self, parent, msg):
    self.error_message.append("%s in %s" % (msg, parent))

  def _Validate(self, schema, yaml_obj, parent):
    if isinstance(schema, list):
      return self._ValidateList(schema, yaml_obj, parent)
    if isinstance(schema, dict):
      return self._ValidateDict(schema, yaml_obj, parent)
    return self._ValidateScalar(schema, yaml_obj, parent)

  def _ValidateList(self, schema, yaml_obj, parent):
    if not isinstance(schema, list):
      raise Exception("Expected schema to be a list, but was: %s" % schema)
    if not len(schema) == 1:
      raise Exception("Array schema should have exactly one element."
                      " Schema = %s" % schema)
    if yaml_obj == None and schema[0] == "OPTIONAL":
      return True
    if not isinstance(yaml_obj, list):
      self._AddError(parent,
                     "Expect yaml_obj to be a list but it is: %s" % yaml_obj)
      return False
    for i in range(len(yaml_obj)):
      obj = yaml_obj[i]
      if not self._Validate(schema[0], obj, "%s[%d]" % (parent, i)):
        return False
    return True

  def _ValidateDict(self, schema, yaml_obj, parent):
    if not isinstance(schema, dict):
      raise Exception("Expected schema to be a dictionary but was: %s" % schema)
    if not isinstance(yaml_obj, dict):
      self._AddError(parent,
                     "Expect yaml_obj to be a dict but it is: %s" % yaml_obj)
      return False
    for k in yaml_obj:
      if not k in schema:
        self._AddError(parent, "%s is not in the schema" % k)
        return False
      if not self._Validate(schema[k], yaml_obj[k], "%s.%s" % (parent, k)):
        return False
    # after this point we just need to validate that missing keys are OPTIONAL
    for k in schema:
      if not k in yaml_obj:
        if not self._Validate(schema[k], None, "%s.%s" % (parent, k)):
          return False
    return True

  def _isScalar(self, obj):
    return not (isinstance(obj, dict) or isinstance(obj, list))

  def _ValidateScalar(self, schema, yaml_obj, parent):
    if not self._isScalar(schema):
      raise Exception("Expected schema to be a scalar but was: %s" % schema)
    if schema == "OPTIONAL":
      if yaml_obj == None:
        return True
      if self._isScalar(yaml_obj):
        return True
      self._AddError(parent,
                     "found %s but expected an optional scalar" % yaml_obj)
      return False
    if schema == "REQUIRED":
      if not self._isScalar(yaml_obj):
        self._AddError(parent, "found %s but expected a scalar" % yaml_obj)
        return False
      if yaml_obj:
        return True
      self._AddError(parent, "REQUIRED field missing")
      return False
    if schema.startswith("UNIQUE"):
      key = schema[len("UNIQUE "):]
      if not self._isScalar(yaml_obj):
        self._AddError(parent,
                       "found %s but expected a UNIQUE scalar" % yaml_obj)
        return False
      if not key in self.unique_values:
        self.unique_values[key] = set()
      if yaml_obj in self.unique_values[key]:
        self._AddError(parent,
                       "Duplicate Value %s in UNIQUE %s" % (yaml_obj, key))
        return False
      self.unique_values[key].add(yaml_obj)
      return True
    if schema.startswith("AUTO_INC"):
      key = schema[len("AUTO_INC "):]
      if not key in self.counters:
        self.counters[key] = {'start': 0, 'set': set()}
      if yaml_obj:
        if not isinstance(yaml_obj, int):
          self._AddError(parent,
                         "found %s but expected an AUTO_INC int" % yaml_obj)
          return False
        if yaml_obj in self.counters[key]['set']:
          self._AddError(parent, "duplicate AUTO_INC %s found" % yaml_obj)
          return False
        self.counters[key]['start'] = max(self.counters[key]['start'], yaml_obj + 1)
        self.counters[key]['set'].add(yaml_obj)
      return True
