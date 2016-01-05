import models
import yaml
import logging
import yayv
import schemas
import models

try:
  from google.appengine.ext import ndb
except:
  logging.info("google.appengine.ext not found. "
                "We must be running in a unit test.")
  import fake_ndb
  ndb = fake_ndb.FakeNdb()

class Checker(object):
  def __init__(self):
    self.error_check_status = 'OK'
    self.error_check_detail = ''

  # Modules that change admin setup data should call this
  # with status = 'UNKNOWN'.
  @classmethod
  def setStatus(self, institution, session, status = 'UNKNOWN'):
    models.ErrorCheck.Store(institution, session, status)

  @classmethod
  def getStatus(self, institution, session):
    return models.ErrorCheck.Fetch(institution, session)

  # Returns two values:
  #   error_check_status: 'OK' if all tests pass
  #                       'FAIL' if any single test fails
  #   error_check_detail: String containing detailed results
  #                       for ALL tests.
  # Sets datastore to value of error_check_status
  def Run(self, institution, session):
    dayparts = models.Dayparts.Fetch(institution, session)
    classes = models.Classes.Fetch(institution, session)
    students = models.Students.Fetch(institution, session)
    requirements = models.Requirements.Fetch(institution, session)
    class_groups = models.GroupsClasses.Fetch(institution, session)
    student_groups = models.GroupsStudents.Fetch(institution, session)

    valid_dayparts = schemas.dayparts.IsValid(dayparts)
    valid_classes = schemas.classes.IsValid(classes)
    valid_students = schemas.students.IsValid(students)
    valid_requirements = schemas.requirements.IsValid(requirements)
    valid_class_groups = schemas.class_groups.IsValid(class_groups)
    valid_student_groups = schemas.student_groups.IsValid(student_groups)

    self.error_check_detail += '\nValidate Dayparts: ' +\
      self._Validate(dayparts, valid_dayparts)
    self.error_check_detail += '\nValidate Classes: ' +\
      self._Validate(classes, valid_classes)
    self.error_check_detail += '\nValidate Students: ' +\
      self._Validate(students, valid_students)
    self.error_check_detail += '\nValidate Requirements: ' +\
      self._Validate(requirements, valid_requirements)
    self.error_check_detail += '\nValidate Class Groups: ' +\
      self._Validate(class_groups, valid_class_groups)
    self.error_check_detail += '\nValidate Student Groups: ' +\
      self._Validate(student_groups, valid_student_groups)
    self.error_check_detail += '\n\nCheck Class dayparts against Dayparts: ' +\
      self._CheckClassDayparts(dayparts, valid_dayparts, classes, valid_classes)
    self.error_check_detail += '\n\nCheck if all Dayparts are used: ' +\
      self._CheckDaypartsUsed(dayparts, valid_dayparts, classes, valid_classes)
    self.error_check_detail += '\n\nCheck Class student groups against Student Groups: ' +\
      self._CheckClassStudentGroups(student_groups, valid_student_groups, classes, valid_classes)
    self.error_check_detail += '\n\nCheck if all Student Groups are used: ' +\
      self._CheckStudentGroupsUsed(student_groups, valid_student_groups, classes, valid_classes)
    self.error_check_detail += '\n\nCheck Class student emails against Students: ' +\
      self._CheckClassEmails(students, valid_students, classes, valid_classes)
    self.error_check_detail += '\n\nCheck Class current_grade against Student current_grade: ' +\
      self._CheckCurrentGrade(students, valid_students, classes, valid_classes)
        
    self.setStatus(institution, session, self.error_check_status)
    return self.error_check_status, self.error_check_detail

  def _Validate(self, yaml_str, valid_schema):
    if not yaml_str:
      self.error_check_status = 'FAIL'
      return('Yaml string not found. Check your Setup.')
    if not valid_schema:
      self.error_check_status = 'FAIL'
      return('Invalid yaml string. Check your Setup.')
    return('OK')

  def _CheckClassDayparts(self, dayparts, valid_dayparts, classes, valid_classes):
    if not dayparts:
      self.error_check_status = 'FAIL'
      return('Dayparts yaml string not found. Check your Setup.')
    if not valid_dayparts:
      self.error_check_status = 'FAIL'
      return('Invalid Dayparts yaml string. Check your Setup.')
    if not classes:
      self.error_check_status = 'FAIL'
      return('Classes yaml string not found. Check your Setup.')
    if not valid_classes:
      self.error_check_status = 'FAIL'
      return('Invalid Classes yaml string. Check your Setup.')
    dayparts = yaml.load(dayparts)
    classes = yaml.load(classes)
    try:
      _ = [c for c in classes]
    except TypeError:
      self.error_check_status = 'FAIL'
      return('Expecting classes to be a list.')
    errMsg = ''
    daypart_set = set([dp['name'] for dp in dayparts])
    for c in classes:
      for cdaypart in [s['daypart'] for s in c['schedule']]:
        if cdaypart not in daypart_set:
          errMsg += '\nMismatching daypart <<' + cdaypart + '>>'\
            + ' in ' + c['name'] + ', ID ' + str(c['id'])
    if errMsg:
      self.error_check_status = 'FAIL'
      return(errMsg)
    return('OK')

  def _CheckDaypartsUsed(self, dayparts, valid_dayparts, classes, valid_classes):
    if not dayparts:
      self.error_check_status = 'FAIL'
      return('Dayparts yaml string not found. Check your Setup.')
    if not valid_dayparts:
      self.error_check_status = 'FAIL'
      return('Invalid Dayparts yaml string. Check your Setup.')
    if not classes:
      self.error_check_status = 'FAIL'
      return('Classes yaml string not found. Check your Setup.')
    if not valid_classes:
      self.error_check_status = 'FAIL'
      return('Invalid Classes yaml string. Check your Setup.')
    dayparts = yaml.load(dayparts)
    classes = yaml.load(classes)
    try:
      _ = [c for c in classes]
    except TypeError:
      return('Expecting classes to be a list.')
    errMsg = ''
    # There is potential for many duplicate dayparts in class schedules.
    # Making class_dps a set will greatly reduce the list.
    class_dps = set([s['daypart'] for c in classes for s in c['schedule']])
    for dp in dayparts:
      if dp['name'] not in class_dps:
        errMsg += '\nDaypart <<' + dp['name'] + '>> is not referenced in any classes.'
    if errMsg:
      self.error_check_status = 'FAIL'
      return(errMsg)
    return('OK')

  def _CheckClassStudentGroups(self, student_groups, valid_student_groups, classes, valid_classes):
    if not student_groups:
      self.error_check_status = 'FAIL'
      return('Student Groups yaml string not found. Check your Setup.')
    if not valid_student_groups:
      self.error_check_status = 'FAIL'
      return('Invalid Student Groups yaml string. Check your Setup.')
    if not classes:
      self.error_check_status = 'FAIL'
      return('Classes yaml string not found. Check your Setup.')
    if not valid_classes:
      self.error_check_status = 'FAIL'
      return('Invalid Classes yaml string. Check your Setup.')
    student_groups = yaml.load(student_groups)
    classes = yaml.load(classes)
    try:
      _ = [c for c in classes]
    except TypeError:
      self.error_check_status = 'FAIL'
      return('Expecting classes to be a list.')
    errMsg = ''
    sg_set = set([sg['group_name'] for sg in student_groups])
    for c in classes:
      for student_group in [p['group'] for p in c['prerequisites'] if 'group' in p]:
        if student_group not in sg_set:
          errMsg += '\nReferring to non-existent student group <<' + student_group + '>>'\
            + ' in ' + c['name'] + ', ID ' + str(c['id'])
    if errMsg:
      self.error_check_status = 'FAIL'
      return(errMsg)
    return('OK')

  def _CheckStudentGroupsUsed(self, student_groups, valid_student_groups, classes, valid_classes):
    if not student_groups:
      self.error_check_status = 'FAIL'
      return('Student Groups yaml string not found. Check your Setup.')
    if not valid_student_groups:
      self.error_check_status = 'FAIL'
      return('Invalid Student Groups yaml string. Check your Setup.')
    if not classes:
      self.error_check_status = 'FAIL'
      return('Classes yaml string not found. Check your Setup.')
    if not valid_classes:
      self.error_check_status = 'FAIL'
      return('Invalid Classes yaml string. Check your Setup.')
    student_groups = yaml.load(student_groups)
    classes = yaml.load(classes)
    try:
      _ = [c for c in classes]
    except TypeError:
      return('Expecting classes to be a list.')
    errMsg = ''
    class_student_groups = set([p['group'] for c in classes for p in c['prerequisites'] if 'group' in p])
    for sg in student_groups:
      if sg['group_name'] not in class_student_groups:
        errMsg += '\nStudent Group <<' + sg['group_name'] + '>> is not referenced in any classes.'
    if errMsg:
      self.error_check_status = 'FAIL'
      return(errMsg)
    return('OK')

  def _CheckClassEmails(self, students, valid_students, classes, valid_classes):
    if not students:
      self.error_check_status = 'FAIL'
      return('Students yaml string not found. Check your Setup.')
    if not valid_students:
      self.error_check_status = 'FAIL'
      return('Invalid Student yaml string. Check your Setup.')
    if not classes:
      self.error_check_status = 'FAIL'
      return('Classes yaml string not found. Check your Setup.')
    if not valid_classes:
      self.error_check_status = 'FAIL'
      return('Invalid Classes yaml string. Check your Setup.')
    students = yaml.load(students)
    classes = yaml.load(classes)
    try:
      _ = [c for c in classes]
    except TypeError:
      self.error_check_status = 'FAIL'
      return('Expecting classes to be a list.')
    errMsg = ''
    students_set = set([s['email'] for s in students])
    for c in classes:
      for student_email in [p['email'] for p in c['prerequisites'] if 'email' in p]:
        if student_email not in students_set:
          errMsg += '\nReferring to non-existent student email <<' + student_email + '>>'\
            + ' in ' + c['name'] + ', ID ' + str(c['id'])
    if errMsg:
      self.error_check_status = 'FAIL'
      return(errMsg)
    return('OK')

  def _CheckCurrentGrade(self, students, valid_students, classes, valid_classes):
    if not students:
      self.error_check_status = 'FAIL'
      return('Students yaml string not found. Check your Setup.')
    if not valid_students:
      self.error_check_status = 'FAIL'
      return('Invalid Student yaml string. Check your Setup.')
    if not classes:
      self.error_check_status = 'FAIL'
      return('Classes yaml string not found. Check your Setup.')
    if not valid_classes:
      self.error_check_status = 'FAIL'
      return('Invalid Classes yaml string. Check your Setup.')
    students = yaml.load(students)
    classes = yaml.load(classes)
    try:
      _ = [c for c in classes]
    except TypeError:
      self.error_check_status = 'FAIL'
      return('Expecting classes to be a list.')
    errMsg = ''
    student_grade_set = set([s['current_grade'] for s in students])
    for c in classes:
      for class_grade in [p['current_grade'] for p in c['prerequisites'] if 'current_grade' in p]:
        if class_grade not in student_grade_set:
          errMsg += '\nNo student belongs to current_grade <<' + str(class_grade) + '>>'\
            + ' in ' + c['name'] + ', ID ' + str(c['id']) + '.'
    class_grade_set = set([p['current_grade'] for c in classes for p in c['prerequisites'] if 'current_grade' in p])
    for s in students:
      if s['current_grade'] not in class_grade_set:
        errMsg += '\nStudent grade <<' + str(s['current_grade']) + '>>'\
          + ' for ' +  s['email'] + ' is not referenced in any class.'
    if errMsg:
      self.error_check_status = 'FAIL'
      return(errMsg)
    return('OK')
