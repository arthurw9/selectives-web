import models
import yaml
import logging
import yayv
import schemas

try:
  from google.appengine.ext import ndb
except:
  logging.info("google.appengine.ext not found. "
                "We must be running in a unit test.")
  import fake_ndb
  ndb = fake_ndb.FakeNdb()

# Returns two values.
# setup_msg: 'OK' if all tests pass, 'FAIL' if any single test fails.
# error_chk: String containing detailed results for ALL tests.
def CheckAll(institution, session):
  setup_msg = 'OK'
  result = Validate(institution, session, models.Dayparts, schemas.dayparts)
  if result != 'OK':
    setup_msg = 'FAIL'
  error_chk = 'Validate Dayparts: ' + result
  result = Validate(institution, session, models.Classes, schemas.classes)
  if result != 'OK':
    setup_msg = 'FAIL'
  error_chk += '\nValidate Classes: ' + result
  result = Validate(institution, session, models.Students, schemas.students)
  if result != 'OK':
    setup_msg = 'FAIL'
  error_chk += '\nValidate Students: ' + result
  result = Validate(institution, session, models.Requirements, schemas.requirements)
  if result != 'OK':
    setup_msg = 'FAIL'
  error_chk += '\nValidate Requirements: ' + result
  result = Validate(institution, session, models.GroupsClasses, schemas.class_groups)
  if result != 'OK':
    setup_msg = 'FAIL'
  error_chk += '\nValidate Class Groups: ' + result
  result = Validate(institution, session, models.GroupsStudents, schemas.student_groups)
  if result != 'OK':
    setup_msg = 'FAIL'
  error_chk += '\nValidate Student Groups: ' + result
  result = CheckClassDayparts(institution, session)
  if result != 'OK':
    setup_msg = 'FAIL'
  error_chk += '\n\nCheck Class dayparts against Dayparts: ' + result
  result = CheckDaypartsUsed(institution, session)
  if result != 'OK':
    setup_msg = 'FAIL'
  error_chk += '\n\nCheck if all Dayparts are used: ' + result
  result = CheckClassStudentGroups(institution, session)
  if result != 'OK':
    setup_msg = 'FAIL'
  error_chk += '\n\nCheck Class student groups against Student Groups: ' + result
  result = CheckStudentGroupsUsed(institution, session)
  if result != 'OK':
    setup_msg = 'FAIL'
  error_chk += '\n\nCheck if all Student Groups are used: ' + result
  result = CheckClassEmails(institution, session)
  if result != 'OK':
    setup_msg = 'FAIL'
  error_chk += '\n\nCheck Class student emails against Students: ' + result
  result = CheckCurrentGrade(institution, session)
  if result != 'OK':
    setup_msg = 'FAIL'
  error_chk += '\n\nCheck Class current_grade against Student current_grade: ' + result
  return setup_msg, error_chk

def Validate(institution, session, model, schema):
  yaml_str = model.Fetch(institution, session)
  if not yaml_str:
    return('Yaml string not found. Check your Setup.')
  if not schema.IsValid(yaml_str):
    return('Invalid yaml string. Check your Setup.')
  return('OK')

def CheckClassDayparts(institution, session):
  dayparts = models.Dayparts.Fetch(institution, session)
  if not dayparts:
    return('Dayparts yaml string not found. Check your Setup.')
  if not schemas.dayparts.IsValid(dayparts):
    return('Invalid Dayparts yaml string. Check your Setup.')
  dayparts = yaml.load(dayparts)
  classes = models.Classes.Fetch(institution, session)
  if not classes:
    return('Classes yaml string not found. Check your Setup.')
  if not schemas.classes.IsValid(classes):
    return('Invalid Classes yaml string. Check your Setup.')
  classes = yaml.load(classes)
  try:
    _ = [c for c in classes]
  except TypeError:
    return('Expecting classes to be a list.')
  errMsg = ''
  for c in classes:
    for cdaypart in [s['daypart'] for s in c['schedule']]:
      if cdaypart not in [dp['name'] for dp in dayparts]:
        errMsg += '\nMismatching daypart <<' + cdaypart + '>>'\
          + ' in ' + c['name'] + ', ID ' + str(c['id'])
  if errMsg:
    return(errMsg)
  return('OK')

def CheckDaypartsUsed(institution, session):
  dayparts = models.Dayparts.Fetch(institution, session)
  if not dayparts:
    return('Dayparts yaml string not found. Check your Setup.')
  if not schemas.dayparts.IsValid(dayparts):
    return('Invalid Dayparts yaml string. Check your Setup.')
  dayparts = yaml.load(dayparts)
  classes = models.Classes.Fetch(institution, session)
  if not classes:
    return('Classes yaml string not found. Check your Setup.')
  if not schemas.classes.IsValid(classes):
    return('Invalid Classes yaml string. Check your Setup.')
  classes = yaml.load(classes)
  try:
    _ = [c for c in classes]
  except TypeError:
    return('Expecting classes to be a list.')
  errMsg = ''
  class_dps = [s['daypart'] for c in classes for s in c['schedule']]
  for dp in dayparts:
    if dp['name'] not in class_dps:
      errMsg += '\nDaypart <<' + dp['name'] + '>> is not referenced in any classes.'
  if errMsg:
    return(errMsg)
  return('OK')

def CheckClassStudentGroups(institution, session):
  student_groups = models.GroupsStudents.Fetch(institution, session)
  if not student_groups:
    return('Student Groups yaml string not found. Check your Setup.')
  if not schemas.student_groups.IsValid(student_groups):
    return('Invalid Student Groups yaml string. Check your Setup.')
  student_groups = yaml.load(student_groups)
  classes = models.Classes.Fetch(institution, session)
  if not classes:
    return('Classes yaml string not found. Check your Setup.')
  if not schemas.classes.IsValid(classes):
    return('Invalid Classes yaml string. Check your Setup.')
  classes = yaml.load(classes)
  try:
    _ = [c for c in classes]
  except TypeError:
    return('Expecting classes to be a list.')
  errMsg = ''
  for c in classes:
    for student_group in [p['group'] for p in c['prerequisites'] if 'group' in p]:
      if student_group not in [sg['group_name'] for sg in student_groups]:
        errMsg += '\nReferring to non-existent student group <<' + student_group + '>>'\
          + ' in ' + c['name'] + ', ID ' + str(c['id'])
  if errMsg:
    return(errMsg)
  return('OK')

def CheckStudentGroupsUsed(institution, session):
  student_groups = models.GroupsStudents.Fetch(institution, session)
  if not student_groups:
    return('Student Groups yaml string not found. Check your Setup.')
  if not schemas.student_groups.IsValid(student_groups):
    return('Invalid Student Groups yaml string. Check your Setup.')
  student_groups = yaml.load(student_groups)
  classes = models.Classes.Fetch(institution, session)
  if not classes:
    return('Classes yaml string not found. Check your Setup.')
  if not schemas.classes.IsValid(classes):
    return('Invalid Classes yaml string. Check your Setup.')
  classes = yaml.load(classes)
  try:
    _ = [c for c in classes]
  except TypeError:
    return('Expecting classes to be a list.')
  errMsg = ''
  class_student_groups = [p['group'] for c in classes for p in c['prerequisites'] if 'group' in p]
  for sg in student_groups:
    if sg['group_name'] not in class_student_groups:
      errMsg += '\nStudent Group <<' + sg['group_name'] + '>> is not referenced in any classes.'
  if errMsg:
    return(errMsg)
  return('OK')

def CheckClassEmails(institution, session):
  students = models.Students.Fetch(institution, session)
  if not students:
    return('Students yaml string not found. Check your Setup.')
  if not schemas.students.IsValid(students):
    return('Invalid Student yaml string. Check your Setup.')
  students = yaml.load(students)
  classes = models.Classes.Fetch(institution, session)
  if not classes:
    return('Classes yaml string not found. Check your Setup.')
  if not schemas.classes.IsValid(classes):
    return('Invalid Classes yaml string. Check your Setup.')
  classes = yaml.load(classes)
  try:
    _ = [c for c in classes]
  except TypeError:
    return('Expecting classes to be a list.')
  errMsg = ''
  for c in classes:
    for student_email in [p['email'] for p in c['prerequisites'] if 'email' in p]:
      if student_email not in [s['email'] for s in students]:
        errMsg += '\nReferring to non-existent student email <<' + student_email + '>>'\
          + ' in ' + c['name'] + ', ID ' + str(c['id'])
  if errMsg:
    return(errMsg)
  return('OK')

def CheckCurrentGrade(institution, session):
  students = models.Students.Fetch(institution, session)
  if not students:
    return('Students yaml string not found. Check your Setup.')
  if not schemas.students.IsValid(students):
    return('Invalid Student yaml string. Check your Setup.')
  students = yaml.load(students)
  classes = models.Classes.Fetch(institution, session)
  if not classes:
    return('Classes yaml string not found. Check your Setup.')
  if not schemas.classes.IsValid(classes):
    return('Invalid Classes yaml string. Check your Setup.')
  classes = yaml.load(classes)
  try:
    _ = [c for c in classes]
  except TypeError:
    return('Expecting classes to be a list.')
  errMsg = ''
  for c in classes:
    for class_grade in [p['current_grade'] for p in c['prerequisites'] if 'current_grade' in p]:
      if class_grade not in [s['current_grade'] for s in students]:
        errMsg += '\nNo student belongs to current_grade <<' + str(class_grade) + '>>'\
          + ' in ' + c['name'] + ', ID ' + str(c['id']) + '.'
  for s in students:
    if s['current_grade'] not in [p['current_grade'] for c in classes for p in c['prerequisites'] if 'current_grade' in p]:
      errMsg += '\nStudent grade <<' + str(s['current_grade']) + '>>'\
        + ' for ' +  s['email'] + ' is not referenced in any class.'
  if errMsg:
    return(errMsg)
  return('OK')