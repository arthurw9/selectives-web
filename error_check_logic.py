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

    isValid_dayparts = schemas.dayparts.IsValid(dayparts)
    isValid_classes = schemas.classes.IsValid(classes)
    isValid_students = schemas.students.IsValid(students)
    isValid_requirements = schemas.requirements.IsValid(requirements)
    isValid_class_groups = schemas.class_groups.IsValid(class_groups)
    isValid_student_groups = schemas.student_groups.IsValid(student_groups)

    self._Validate(dayparts, isValid_dayparts, 'Dayparts')
    self._Validate(classes, isValid_classes, 'Classes')
    self._Validate(students, isValid_students, 'Students')
    self._Validate(requirements, isValid_requirements, 'Requirements')
    self._Validate(class_groups, isValid_class_groups, 'Class Groups')
    self._Validate(student_groups, isValid_student_groups, 'Student Groups')

    self._CheckClassDayparts(dayparts, isValid_dayparts,
                             classes, isValid_classes)
    self._CheckDaypartsUsed(dayparts, isValid_dayparts,
                            classes, isValid_classes)
    self._CheckClassStudentGroups(student_groups, isValid_student_groups,
                                  classes, isValid_classes)
    self._CheckStudentGroupsUsed(student_groups, isValid_student_groups,
                                 classes, isValid_classes)
    self._CheckClassEmails(students, isValid_students,
                           classes, isValid_classes)
    self._CheckCurrentGrade(students, isValid_students,
                            classes, isValid_classes)
        
    self.setStatus(institution, session, self.error_check_status)
    return self.error_check_status, self.error_check_detail

  def _Validate(self, yaml_str, isValid_schema, name):
    self.error_check_detail += '\nValidate %s: ' % name
    if not yaml_str:
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'yaml string not found, check your Setup.'
      return
    if not isValid_schema:
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid yaml string, check your Setup.'
      return
    self.error_check_detail += 'OK'
    return

  def _CheckClassDayparts(self, dayparts, isValid_dayparts, classes, isValid_classes):
    self.error_check_detail += '\n\nCheck Class dayparts against Dayparts: '
    if not (dayparts and isValid_dayparts):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Dayparts, unable to run this test.'
      return
    if not (classes and isValid_classes):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Classes, unable to run this test.'
      return
    dayparts = yaml.load(dayparts)
    classes = yaml.load(classes)
    try:
      _ = [c for c in classes]
    except TypeError:
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'expect classes to be a list'
      return
    errMsg = ''
    daypart_set = set([dp['name'] for dp in dayparts])
    for c in classes:
      for cdaypart in [s['daypart'] for s in c['schedule']]:
        if cdaypart not in daypart_set:
          errMsg += '\nMismatching daypart <<' + cdaypart + '>>'\
            + ' in ' + c['name'] + ', ID ' + str(c['id'])
    if errMsg:
      self.error_check_status = 'FAIL'
      self.error_check_detail += errMsg
      return
    self.error_check_detail += 'OK'

  def _CheckDaypartsUsed(self, dayparts, isValid_dayparts, classes, isValid_classes):
    self.error_check_detail += '\n\nCheck if all Dayparts are used: '
    if not (dayparts and isValid_dayparts):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Dayparts, unable to run this test.'
      return
    if not (classes and isValid_classes):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Classes, unable to run this test.'
      return
    dayparts = yaml.load(dayparts)
    classes = yaml.load(classes)
    try:
      _ = [c for c in classes]
    except TypeError:
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'expect classes to be a list'
      return
    errMsg = ''
    # There is potential for many duplicate dayparts in class schedules.
    # Making class_dps a set will greatly reduce the list.
    class_dps = set([s['daypart'] for c in classes for s in c['schedule']])
    for dp in dayparts:
      if dp['name'] not in class_dps:
        errMsg += '\nDaypart <<' + dp['name'] + '>> is not referenced in any classes.'
    if errMsg:
      self.error_check_status = 'FAIL'
      self.error_check_detail += errMsg
      return
    self.error_check_detail += 'OK'

  def _CheckClassStudentGroups(self, student_groups, isValid_student_groups, classes, isValid_classes):
    self.error_check_detail += '\n\nCheck Class student groups against Student Groups: '
    if not (student_groups and isValid_student_groups):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Student Groups, unable to run this test.'
      return
    if not (classes and isValid_classes):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Classes, unable to run this test.'
      return
    student_groups = yaml.load(student_groups)
    classes = yaml.load(classes)
    try:
      _ = [c for c in classes]
    except TypeError:
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'expect classes to be a list'
      return
    errMsg = ''
    sg_set = set([sg['group_name'] for sg in student_groups])
    for c in classes:
      for student_group in [p['group'] for p in c['prerequisites'] if 'group' in p]:
        if student_group not in sg_set:
          errMsg += '\nReferring to non-existent student group <<' + student_group + '>>'\
            + ' in ' + c['name'] + ', ID ' + str(c['id'])
    if errMsg:
      self.error_check_status = 'FAIL'
      self.error_check_detail += errMsg
      return
    self.error_check_detail += 'OK'

  def _CheckStudentGroupsUsed(self, student_groups, isValid_student_groups, classes, isValid_classes):
    self.error_check_detail += '\n\nCheck if all Student Groups are used: '
    if not (student_groups and isValid_student_groups):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Student Groups, unable to run this test.'
      return
    if not (classes and isValid_classes):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Classes, unable to run this test.'
      return
    student_groups = yaml.load(student_groups)
    classes = yaml.load(classes)
    try:
      _ = [c for c in classes]
    except TypeError:
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'expect classes to be a list'
      return
    errMsg = ''
    class_student_groups = set([p['group'] for c in classes for p in c['prerequisites'] if 'group' in p])
    for sg in student_groups:
      if sg['group_name'] not in class_student_groups:
        errMsg += '\nStudent Group <<' + sg['group_name'] + '>> is not referenced in any classes.'
    if errMsg:
      self.error_check_status = 'FAIL'
      self.error_check_detail += errMsg
      return
    self.error_check_detail += 'OK'

  def _CheckClassEmails(self, students, isValid_students, classes, isValid_classes):
    self.error_check_detail += '\n\nCheck Class student emails against Students: '
    if not (students and isValid_students):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Students, unable to run this test.'
      return
    if not (classes and isValid_classes):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Classes, unable to run this test.'
      return
    students = yaml.load(students)
    classes = yaml.load(classes)
    try:
      _ = [c for c in classes]
    except TypeError:
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'expect classes to be a list'
      return
    errMsg = ''
    students_set = set([s['email'] for s in students])
    for c in classes:
      for student_email in [p['email'] for p in c['prerequisites'] if 'email' in p]:
        if student_email not in students_set:
          errMsg += '\nReferring to non-existent student email <<' + student_email + '>>'\
            + ' in ' + c['name'] + ', ID ' + str(c['id'])
    if errMsg:
      self.error_check_status = 'FAIL'
      self.error_check_detail += errMsg
      return
    self.error_check_detail += 'OK'

  def _CheckCurrentGrade(self, students, isValid_students, classes, isValid_classes):
    self.error_check_detail += '\n\nCheck Class current_grade against Student current_grade: '
    if not (students and isValid_students):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Students, unable to run this test.'
      return
    if not (classes and isValid_classes):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Classes, unable to run this test.'
      return
    students = yaml.load(students)
    classes = yaml.load(classes)
    try:
      _ = [c for c in classes]
    except TypeError:
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'expect classes to be a list'
      return
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
      self.error_check_detail += errMsg
      return
    self.error_check_detail += 'OK'
