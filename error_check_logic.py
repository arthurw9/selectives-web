"""
Compare data from one field against another.
If no match, most likely a Setup data entry error has occurred.

Classes/schedule/daypart              <--> Dayparts/name
Classes/prerequisite/group            <--> StudentGroups/group_name
Classes/prerequisite/current_grade    <--> Students/current_grade
Classes/prerequisite/email             --> Students/email
StudentGroups/emails                   --> Students/email
AutoRegister/applies_to/email & exempt --> Students/email
AutoRegister/applies_to/group          --> StudentGroups/group_name
AutoRegister/applies_to/current_grade  --> Students/current_grade
AutoRegister/class                     --> Classes/name
  & AutoRegister/class_id                    & Classes/id
ServingRules/allow/current_grade       --> Students/current_grade
  & ServingRules/allow/current_homeroom      & Students/current_homeroom
  & ServingRules/allow/email                 & Students/email
Student/email                - contains correct graduation year
Students/current_grade       - output number of students in each grade
Students/current_homeroom    - output number of students in each homeroom

TODO
Schedule/email                         --> Student/email
Roster/email                           --> Student/email
  Deleted student from Setup or changed student email, but student's
  email is still in schedule and rosters.

TODO (Only if we get Requirements working and not decide to implement
it some other way.)
ClassGroups/classes/name               --> Classes/name
  & ClassGroups/classes/id                  & Classes/id
Requirements/applies_to/email          --> Students/email
  & Requirements/exempt                     & Students/email
Requirements/current_grade             --> Students/current_grade
Requirements/group                     --> StudentGroups/group_name
Requirements/class_or_group_options    --> Classes/id
Requirements/class_or_group_options    --> ClassGroups/name
"""

import models
import yaml
import logging
import yayv
import schemas
from datetime import date

try:
  from google.appengine.ext import ndb
except:
  logging.info("google.appengine.ext not found. "
                "We must be running in a unit test.")
  import fake_ndb
  ndb = fake_ndb.FakeNdb()

# Increase this value manually when datastore upgrade is needed
# CURRENT_DB_VERSION = 0, Yaml format
# CURRENT_DB_VERSION = 1, Json eliminates yaml.load for performance
CURRENT_DB_VERSION = 1

class Checker(object):

  def __init__(self, institution, session):
    self.error_check_status = 'OK'
    self.error_check_detail = ''
    self.institution = institution
    self.session = session

  # Modules that change admin setup data should call this
  # with status = 'UNKNOWN'.
  @classmethod
  def setStatus(cls, institution, session, status = 'UNKNOWN'):
    models.ErrorCheck.Store(institution, session, status)

  @classmethod
  def getStatus(cls, institution, session):
    if (cls.DBUpdateNeeded(institution, session)):
      return 'DB_UPDATE_NEEDED'
    else:
      return models.ErrorCheck.Fetch(institution, session)

  @classmethod
  def DBUpdateNeeded(cls, institution, session):
    stored_version = models.DBVersion.Fetch(institution, session)
    return (stored_version != CURRENT_DB_VERSION)

  @classmethod
  def setDBVersion(cls, institution, session, status = CURRENT_DB_VERSION):
    models.DBVersion.Store(institution, session, status)

  def RunUpgradeScript(self):
    dayparts = models.Dayparts.Fetch(self.institution, self.session)
    models.Dayparts.store(self.institution, self.session, dayparts)

    classes = models.Classes.Fetch(self.institution, self.session)
    models.Classes.store(self.institution, self.session, classes)

    students = models.Students.Fetch(self.institution, self.session)
    models.Students.store(self.institution, self.session, students)

    #requirements = models.Requirements.Fetch(self.institution, self.session)
    #models.Requirements.store(self.institution, self.session, requirements)

    #groups_classes = models.GroupsClasses.Fetch(self.institution, self.session)
    #models.GroupsClasses.store(self.institution, self.session, groups_classes)

    groups_students = models.GroupsStudents.Fetch(self.institution, self.session)
    models.GroupsStudents.store(self.institution, self.session, groups_students)

    self.setDBVersion(self.institution, self.session, CURRENT_DB_VERSION)

  def ValidateSetup(self):
    """
    Returns two values:
      error_check_status: 'OK' if all tests pass
                          'FAIL' if any test fails
      error_check_detail: String containing detailed results for all tests
    Sets datastore to value of error_check_status
    """
    dayparts = models.Dayparts.Fetch(self.institution, self.session)
    classes = models.Classes.Fetch(self.institution, self.session)
    students = models.Students.Fetch(self.institution, self.session)
    #requirements = models.Requirements.Fetch(self.institution, self.session)
    #class_groups = models.GroupsClasses.Fetch(self.institution, self.session)
    student_groups = models.GroupsStudents.Fetch(self.institution, self.session)
    auto_register = models.AutoRegister.Fetch(self.institution, self.session)
    serving_rules = models.ServingRules.Fetch(self.institution, self.session)

    isValid_dayparts = schemas.Dayparts().IsValid(dayparts)
    isValid_classes = schemas.Classes().IsValid(classes)
    isValid_students = schemas.Students().IsValid(students)
    #isValid_requirements = schemas.Requirements().IsValid(requirements)
    #isValid_class_groups = schemas.ClassGroups().IsValid(class_groups)
    isValid_student_groups = schemas.StudentGroups().IsValid(student_groups)
    isValid_auto_register = schemas.AutoRegister().IsValid(auto_register)
    isValid_serving_rules = schemas.ServingRules().IsValid(serving_rules)

    self._Validate(dayparts, isValid_dayparts, 'Dayparts')
    self._Validate(classes, isValid_classes, 'Classes')
    self._Validate(students, isValid_students, 'Students')
    #self._Validate(requirements, isValid_requirements, 'Requirements')
    #self._Validate(class_groups, isValid_class_groups, 'Class Groups')
    self._Validate(student_groups, isValid_student_groups, 'Student Groups')
    self._Validate(auto_register, isValid_auto_register, 'Auto Register')
    self._Validate(serving_rules, isValid_serving_rules, "Serving Rules")

    dayparts = models.Dayparts.FetchJson(self.institution, self.session)
    classes = models.Classes.FetchJson(self.institution, self.session)
    students = models.Students.FetchJson(self.institution, self.session)
    #requirements = models.Requirements.FetchJson(self.institution, self.session)
    #class_groups = models.GroupsClasses.FetchJson(self.institution, self.session)
    student_groups = models.GroupsStudents.FetchJson(self.institution, self.session)
    auto_register = models.AutoRegister.FetchJson(self.institution, self.session)
    serving_rules = models.ServingRules.FetchJson(self.institution, self.session)
    
    self._CheckClassDayparts(dayparts, isValid_dayparts,
                             classes, isValid_classes)
    self._CheckClassStudentGroups(student_groups, isValid_student_groups,
                                  classes, isValid_classes)
    self._CheckClassEmails(students, isValid_students,
                           classes, isValid_classes)
    self._CheckCurrentGrade(students, isValid_students,
                            classes, isValid_classes)
    self._CheckStudentGroupEmails(students, isValid_students,
                                  student_groups, isValid_student_groups)
    self._CheckAutoRegisterEmails(students, isValid_students,
                                  auto_register, isValid_auto_register)
    self._CheckAutoRegisterStudentGroups(student_groups, isValid_student_groups,
                                         auto_register, isValid_auto_register)
    self._CheckAutoRegisterGrade(students, isValid_students,
                                 auto_register, isValid_auto_register)
    self._CheckAutoRegisterClasses(classes, isValid_classes,
                                   auto_register, isValid_auto_register)
    self._CheckServingRules(students, isValid_students,
                            serving_rules, isValid_serving_rules)
    self._CheckStudentEmail(students, isValid_students)
    self._PrintNumberStudentsPerGrade(students, isValid_students)
    self._PrintNumberStudentsPerHomeroom(students, isValid_students)
    self.setStatus(self.institution, self.session, self.error_check_status)

    # database upgrade is higher priority than other setup errors
    if (self.DBUpdateNeeded(self.institution, self.session)):
      self.error_check_status = 'DB_UPDATE_NEEDED'
    
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
    """Check that dayparts in every Class schedule match an existing daypart
    from Dayparts. And the converse: if there are dayparts that aren't used in any class schedule.
    Dayparts/name <--> Classes/schedule/daypart
    """
    self.error_check_detail += '\n\nCheck Class dayparts against Dayparts and vice versa: '
    if not (dayparts and isValid_dayparts):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Dayparts, unable to run this test.'
      return
    if not (classes and isValid_classes):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Classes, unable to run this test.'
      return
    # Removing this check everywhere. This error shouldn't occur because
    # we call .IsValid() for each schema type, and .IsValid() tests for
    # isinstance(schema, list) and isinstance(schema, dict)
    # try:
    #   _ = [c for c in classes]
    # except TypeError:
    #   etc...
    errMsg = ''
    daypart_set = set([dp['name'] for dp in dayparts])
    for c in classes:
      for cdaypart in [s['daypart'] for s in c['schedule']]:
        if cdaypart not in daypart_set:
          errMsg += '\nMismatching daypart <<%s>> in %s, ID %d' %\
                    (cdaypart, c['name'], c['id'])
    # There is potential for many duplicate dayparts in class schedules.
    # Making class_dps a set will greatly reduce the list.
    class_dps = set([s['daypart'] for c in classes for s in c['schedule']])
    for dp in dayparts:
      if dp['name'] not in class_dps:
        errMsg += '\nDaypart <<%s>> is not referenced in any class.' % dp['name']
    if errMsg:
      self.error_check_status = 'FAIL'
      self.error_check_detail += errMsg
      return
    self.error_check_detail += 'OK'

  def _CheckClassStudentGroups(self, student_groups, isValid_student_groups, classes, isValid_classes):
    """Run through all the classes and make sure each student group mentioned in a
    prerequisite matches an existing student group. And the converse: Run through
    Student Groups and check if any aren't used in any class schedule.
    StudentGroups/group_name <--> Classes/prerequisite/group
    """
    self.error_check_detail += '\nCheck Class student groups against Student Groups and vice versa: '
    if not (student_groups and isValid_student_groups):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Student Groups, unable to run this test.'
      return
    if not (classes and isValid_classes):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Classes, unable to run this test.'
      return
    errMsg = ''
    sg_set = set([sg['group_name'] for sg in student_groups])
    for c in classes:
      for student_group in [p['group'] for p in c['prerequisites'] if 'group' in p]:
        if student_group not in sg_set:
          errMsg += '\nReferring to non-existent student group <<%s>> in %s, ID %d' %\
                    (student_group, c['name'], c['id'])
    class_student_groups = set([p['group'] for c in classes for p in c['prerequisites'] if 'group' in p])
    for sg in student_groups:
      if sg['group_name'] not in class_student_groups:
        errMsg += '\nStudent Group <<%s>> is not referenced in any class.' %\
                  sg['group_name']
    if errMsg:
      self.error_check_status = 'FAIL'
      self.error_check_detail += errMsg
      return
    self.error_check_detail += 'OK'

  def _CheckCurrentGrade(self, students, isValid_students, classes, isValid_classes):
    """Run through all classes and check that grade levels listed in prerequisites
    match an existing current_grade level in the student list. And the converse.
    Classes/prerequisite/current_grade <--> Students/current_grade
    """
    self.error_check_detail += '\nCheck Class current_grade against Student current_grade and vice versa: '
    if not (students and isValid_students):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Students, unable to run this test.'
      return
    if not (classes and isValid_classes):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Classes, unable to run this test.'
      return
    errMsg = ''
    student_grade_set = set([s['current_grade'] for s in students])
    for c in classes:
      for class_grade in [p['current_grade'] for p in c['prerequisites'] if 'current_grade' in p]:
        if class_grade not in student_grade_set:
          errMsg += '\nNo student belongs to current_grade <<%d>> in %s, ID %d' %\
                    (class_grade, c['name'], c['id'])
    class_grade_set = set([p['current_grade'] for c in classes for p in c['prerequisites'] if 'current_grade' in p])
    for s in students:
      if s['current_grade'] not in class_grade_set:
        errMsg += '\nStudent grade <<%d>> for %s is not referenced in any class.' %\
                  (s['current_grade'], s['email'])
    if errMsg:
      self.error_check_status = 'FAIL'
      self.error_check_detail += errMsg
      return
    self.error_check_detail += 'OK'

  def _CheckClassEmails(self, students, isValid_students, classes, isValid_classes):
    """Run through all classes and check that student emails listed in prerequisites
    match an existing email in the student list.
    Classes/prerequisite/email --> Students/email
    """
    self.error_check_detail += '\nCheck Class student emails against Students: '
    if not (students and isValid_students):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Students, unable to run this test.'
      return
    if not (classes and isValid_classes):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Classes, unable to run this test.'
      return
    errMsg = ''
    students_set = set([s['email'].lower() for s in students])
    for c in classes:
      for student_email in [p['email'] for p in c['prerequisites'] if 'email' in p]:
        if student_email.lower() not in students_set:
          errMsg += '\nReferring to non-existent student email <<%s>> in %s, ID %d' %\
                    (student_email, c['name'], c['id'])
    if errMsg:
      self.error_check_status = 'FAIL'
      self.error_check_detail += errMsg
      return
    self.error_check_detail += 'OK'

  def _CheckStudentGroupEmails(self, students, isValid_students, student_groups, isValid_student_groups):
    """Run through all StudentGroups emails and check they match an existing
    Student email.
    StudentGroups/emails --> Students/email
    """
    self.error_check_detail += '\nCheck Student Group emails against Students: '
    if not (students and isValid_students):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Students, unable to run this test.'
      return
    if not (student_groups and isValid_student_groups):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Student Groups, unable to run this test.'
      return
    errMsg = ''
    students_set = set([s['email'].lower() for s in students])
    for sg in student_groups:
      for student_email in sg['emails']:
        if student_email.lower() not in students_set:
          errMsg += '\nReferring to non-existent student email <<%s>> in %s' %\
                    (student_email, sg['group_name'])
    if errMsg:
      self.error_check_status = 'FAIL'
      self.error_check_detail += errMsg
      return
    self.error_check_detail += 'OK'

  def _CheckAutoRegisterEmails(self, students, isValid_students, auto_register_classes, isValid_auto_register_classes):
    """Run through the AutoRegister classes and check that student emails listed
    in the applies_to and exempt fields matches an existing Student email.
    AutoRegister/applies_to/email & AutoRegister/exempt --> Students/email
    """
    self.error_check_detail += '\nCheck Auto Register student emails against Students: '
    if not (students and isValid_students):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Students, unable to run this test.'
      return
    if not (auto_register_classes and isValid_auto_register_classes):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Auto Register classes, unable to run this test.'
      return
    errMsg = ''
    students_set = set([s['email'].lower() for s in students])
    for c in auto_register_classes:
      for student_email in [el['email'] for el in c['applies_to'] if 'email' in el]:
        if student_email.lower() not in students_set:
          errMsg += '\nReferring to non-existent student email <<%s>> in %s, ID %d' %\
                    (student_email, c['class'], c['id'])
      if 'exempt' in c:
        for student_email in c['exempt']:
          if student_email.lower() not in students_set:
            errMsg += '\nReferring to non-existent student email <<%s>> in %s, ID %d' %\
                      (student_email, c.get('class'), c['id'])
    if errMsg:
      self.error_check_status = 'FAIL'
      self.error_check_detail += errMsg
      return
    self.error_check_detail += 'OK'

  def _CheckAutoRegisterStudentGroups(self, student_groups, isValid_student_groups, auto_register_classes, isValid_auto_register_classes):
    """Run through the Auto Register classes and check that student groups listed
    in the applies_to field matches an existing student group.
    AutoRegister/applies_to/group --> StudentGroups/group_name
    """
    self.error_check_detail += '\nCheck Auto Register Class student groups against Student Groups: '
    if not (student_groups and isValid_student_groups):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Student Groups, unable to run this test.'
      return
    if not (auto_register_classes and isValid_auto_register_classes):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Auto Register Classes, unable to run this test.'
      return
    errMsg = ''
    sg_set = set([sg['group_name'] for sg in student_groups])
    for c in auto_register_classes:
      for student_group in [p['group'] for p in c['applies_to'] if 'group' in p]:
        if student_group not in sg_set:
          errMsg += '\nReferring to non-existent student group <<%s>> in %s, ID %d' %\
                    (student_group, c.get('class'), c['id'])
    if errMsg:
      self.error_check_status = 'FAIL'
      self.error_check_detail += errMsg
      return
    self.error_check_detail += 'OK'

  def _CheckAutoRegisterGrade(self, students, isValid_students, auto_register_classes, isValid_auto_register_classes):
    """Run through the Auto Register classes and check that current_grade listed
    in the applies_to field matches an existing Student current_grade.
    AutoRegister/applies_to/current_grade --> Student/current_grade
    """
    self.error_check_detail += '\nCheck Auto Register current_grade against Students current_grade: '
    if not (students and isValid_students):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Students, unable to run this test.'
      return
    if not (auto_register_classes and isValid_auto_register_classes):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Auto Register classes, unable to run this test.'
      return
    errMsg = ''
    student_grade_set = set([s['current_grade'] for s in students])
    for c in auto_register_classes:
      for current_grade in [el['current_grade'] for el in c['applies_to'] if 'current_grade' in el]:
        if current_grade not in student_grade_set:
          errMsg += '\nReferring to non-existent current_grade <<%s>> in %s, ID %d' %\
                    (current_grade, c.get('class'), c['id'])
    if errMsg:
      self.error_check_status = 'FAIL'
      self.error_check_detail += errMsg
      return
    self.error_check_detail += 'OK'

  def _CheckAutoRegisterClasses(self, classes, isValid_classes, auto_register_classes, isValid_auto_register_classes):
    """Run through the Auto Register classes and class_ids and check if they match
    a name and id from Classes.
    AutoRegister/class --> Classes/name
    AutoRegister/class_id --> Classes/id
    """
    self.error_check_detail += '\nCheck Auto Register Class against Classes: '
    if not (classes and isValid_classes):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Classes, unable to run this test.'
      return
    if not (auto_register_classes and isValid_auto_register_classes):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Auto Register Classes, unable to run this test.'
      return
    errMsg = ''
    c_set = set([(c['name'], c['id']) for c in classes])
    for ac in auto_register_classes:
      if (ac.get('class'), ac['class_id']) not in c_set:
          errMsg += '\nMismatched class and id <<(%s, %d)>>' %\
                    (ac.get('class'), ac['class_id'])
    if errMsg:
      self.error_check_status = 'FAIL'
      self.error_check_detail += errMsg
      return
    self.error_check_detail += 'OK'

  def _CheckServingRules(self, students, isValid_students, serving_rules, isValid_serving_rules):
    """Check each Serving Rule allow type (current_grade, current_homeroom, email) against Students.
    ServingRules/allow/current_grade    --> Students/current_grade
    ServingRules/allow/current_homeroom     Students/current_homeroom
    ServingRules/allow/email                Students/email
    """
    self.error_check_detail += '\nCheck Serving Rules against Students: '
    if not (students and isValid_students):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Students, unable to run this test.'
      return
    if not (serving_rules and isValid_serving_rules):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Serving Rules, unable to run this test.'
      return
    errMsg = ''
    grades_set = set([s['current_grade'] for s in students])
    homerooms_set = set([s['current_homeroom'] for s in students])
    emails_set = set([s['email'].lower() for s in students])
    for s in serving_rules:
      for serving_grade in [a['current_grade'] for a in s['allow'] if 'current_grade' in a]:
        if serving_grade not in grades_set:
          errMsg += '\nReferring to non-existent current_grade <<%d>> in %s' %\
                    (serving_grade, s['name'])
      for serving_homeroom in [a['current_homeroom'] for a in s['allow'] if 'current_homeroom' in a]:
        if serving_homeroom not in homerooms_set:
          errMsg += '\nReferring to non-existent current_homeroom <<%d>> in %s' %\
                    (serving_homeroom, s['name'])
      for serving_email in [a['email'] for a in s['allow'] if 'email' in a]:
        if serving_email.lower() not in emails_set:
          errMsg += '\nReferring to non-existent email <<%s>> in %s' %\
                    (serving_email, s['name'])
    if errMsg:
      self.error_check_status = 'FAIL'
      self.error_check_detail += errMsg
      return
    self.error_check_detail += 'OK'

  def _CheckStudentEmail(self, students, isValid_students, grad_year=0):
    """Check that student email addresses contain the correct two-digit
    graduation year.
    grad_year - optional parameter to specify the 8th grade graduation
                year. If not passed, graduation year will be
                calculated based on today's date. For instance, if
                today is September 2016, an eighth grade email format
                is first.last17@mydiscoveryk8.org,
                seventh grade is first.last18@mydiscoveryk8.org,
                sixth grade is first.last19@mydiscoveryk8.org.
                If today is May 2017, eighth grade will be
                first.last17@mydiscoveryk8.org, and so on.
    """
    self.error_check_detail += '\nCheck graduation year in Student email: '
    if not (students and isValid_students):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Students, unable to run this test.'
      return
    if grad_year == 0:
      curr_year = date.today().year % 100 # just want the last two digits
      if date.today().month in (8,9,10,11,12): # school year starts in August
        grad_8 = curr_year + 1
      else:
        grad_8 = curr_year
    else:
      grad_8 = grad_year % 100 # just want the last two digits
    # 7th and 6th graduation years calculated based on 8th.
    grad_7 = grad_8 + 1
    grad_6 = grad_7 + 1

    errMsg = ""
    for s in students:
      if s['current_grade'] == 8 and str(grad_8)+"@" not in s['email'] or\
         s['current_grade'] == 7 and str(grad_7)+"@" not in s['email'] or\
         s['current_grade'] == 6 and str(grad_6)+"@" not in s['email']:
          errMsg += '\n%dth grade : %s' % (s['current_grade'], s['email'])
    if errMsg:
      self.error_check_status = 'FAIL'
      self.error_check_detail += errMsg
      return
    self.error_check_detail += 'OK'

  def _PrintNumberStudentsPerGrade(self, students, isValid_students):
    """Print the number of students per grade level.
    The admin can use this information to check for gross errors.
    For instance, if there is only one student in a grade, there might be a typo.
    """
    self.error_check_detail += '\n\nGrade level : No. Students '
    if not (students and isValid_students):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Students, unable to run this test.'
      return
    grades_set = set([s['current_grade'] for s in students])
    output = [str(g) + 'th : ' + str(len([s for s in students if s['current_grade'] == g])) for g in grades_set]
    self.error_check_detail += '\n'
    self.error_check_detail += '\n'.join(output)

  def _PrintNumberStudentsPerHomeroom(self, students, isValid_students):
    """Print the number of students per homeroom.
    The admin can use this information to check for gross errors.
    For instance, if there is only one student in a homeroom, there might be a typo.
    """
    self.error_check_detail += '\nHomeroom : No. Students '
    if not (students and isValid_students):
      self.error_check_status = 'FAIL'
      self.error_check_detail += 'invalid Students, unable to run this test.'
      return
    homerooms_set = set([s['current_homeroom'] for s in students])
    output = ['Rm. ' + str(h) + ' : ' + str(len([s for s in students if s['current_homeroom'] == h])) for h in homerooms_set]
    self.error_check_detail += '\n'
    self.error_check_detail += '\n'.join(output)
