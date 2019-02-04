import models
import yaml
import logging
import random
import schemas
try:
  from google.appengine.ext import ndb
except:
  logging.info("google.appengine.ext not found. "
                "We must be running in a unit test.")
  import fake_ndb
  ndb = fake_ndb.FakeNdb()


# Students do not need to see class ID, eligibility, locations.
# Students should not see individual emails which may be on the eligibility list.
# Room numbers may change during registration as we finalize the schedule, so don't display room numbers to students.
# TODO: add proper class_desc instead of just dumping the yaml
def GetHoverText(institution, session, admin_view, c):
  """args:
       admin_view: boolean to hide certain fields from students
       c: dict class object to get description of."""
  class_desc = ''
  if admin_view:
    class_desc += 'Id: ' + str(c['id']) + ' '*6
  class_desc += c['name']
  if 'instructor' in c and c['instructor']:
    class_desc += ' '*6 + 'Instructor: ' + c['instructor']
  class_desc += '\nMax Enrollment: ' + str(c['max_enrollment'])
  class_desc += ' '*6 + 'Meets: '
  for s in c['schedule']:
    class_desc += s['daypart']
    if admin_view:
      if isinstance(s['location'], int):
        class_desc += ' (Rm ' + str(s['location']) + ')'
      else:
        class_desc += ' (' + s['location'] + ')'
    class_desc += ', '
  class_desc = class_desc[:-2] # Remove last comma
  if admin_view:
    class_desc += '\nEligible: '
    if 'prerequisites' in c:
      for p in c['prerequisites']:
        for k in p.keys():
          class_desc += '\n - ' + k + ': '
          if isinstance(p[k], int):
            class_desc += str(p[k])
          else:
            class_desc += p[k]
    else:
      class_desc += 'All'
  r = models.ClassRoster.FetchEntity(institution, session, c['id'])
  students = models.Students.FetchJson(institution, session)
  if (r['emails']):
    class_desc += '\n\nNumber Enrolled: ' + str(len(r['emails']))
    student_names = GetStudentNamesSorted(students, r['emails'])
    for s in student_names:
      class_desc += '\n   ' + s
  return class_desc

def GetStudentNamesSorted(students, roster_emails):
  if not students:
    return []
  roster_names = []
  students_by_email = {}
  for s in students:
    students_by_email[s['email']] = s
  for roster_email in roster_emails:
    try:
      s = students_by_email[roster_email]
    except KeyError:
      logging.fatal("HoverText - invalid student in roster!")
      roster_names.append(roster_email)
    else:
      roster_names.append(s['first'] + ' ' +
                          s['last'] + ' ' +
                          str(s['current_homeroom']))
  roster_names.sort()
  return roster_names

def FindUser(user_email, user_list):
  # is user_list iterable?
  try:
    _ = (e for e in user_list)
  except TypeError:
    return None
  for user in user_list:
    if user_email == user['email'].lower():
      return user
  return None

def StudentAllowedPageTypes(institution, session, student, serving_rules):
  """ Returns list containing types of pages student is allowed to access. """
  """ For example, all page types allowed returns """
  """ ['materials', 'schedule', 'preferences', 'verification'] """
  """ No page types allowed returns [] """
  pt = []
  for serving_rule in serving_rules:
    if serving_rule['allow']: # check that allow for this rule is not blank
      for eligible in serving_rule['allow']:
        if 'email' in eligible:
          if student['email'].lower() == eligible['email'].lower():
            pt.append(serving_rule['name'])
            break
        if 'current_homeroom' in eligible:
          if student['current_homeroom'] == eligible['current_homeroom']:
            pt.append(serving_rule['name'])
            break
        if 'current_grade' in eligible:
          if student['current_grade'] == eligible['current_grade']:
            pt.append(serving_rule['name'])
            break
  return pt

def StudentIsEligibleForClass(institution, session, student, c):
  """returns True if student is eligible for class c."""
  if not c['prerequisites']:
    return True
  for prereq in c['prerequisites']:
    # email match takes highest priority
    if 'email' in prereq:
      if student['email'] == prereq['email']:
        return True
      continue
    # current grade can disqualify students but if used with a student group
    # then the student group must match too.
    if 'current_grade' in prereq:
      if not student['current_grade'] == prereq['current_grade']:
        continue
    if not 'group' in prereq:
      # if we got here then only the grade was specified and it matched.
      return True
    # this prerequisite uses a student group. Let's look up the group.
    eligible_group_name = prereq['group']
    student_groups = models.GroupsStudents.FetchJson(institution, session)
    if not student_groups:
      # Error in setup: prerequisite uses a student group but no groups
      # exist yet. Admin should have run error check and caught
      # this error.
      continue
    for group in student_groups:
      if group['group_name'] == eligible_group_name:
        # We found the group. Let's see if the student is in the group.
        for email in group['emails']:
          if student['email'] == email:
            return True
        continue
    # we didn't find the student group. This is an error.
    # TODO: figure out how to tell the user about this error.
    continue
  # none of the prerequisites were met. Return false.
  return False


def EligibleClassIdsForStudent(institution, session, student, classes):
  """Return the set of class ids that the student is eligible to take."""
  class_ids = []
  for c in classes:
    if StudentIsEligibleForClass(institution, session, student, c):
      class_id = str(c['id'])
      class_ids.append(class_id)
  return class_ids


class _ClassRoster(object):
  """Handles adding and removing emails from a class roster.
  Doesn't update the student schedule."""

  def __init__(self, institution, session, class_obj):
    self.institution = institution
    self.session = session
    self.class_obj = class_obj
    new_class_id = class_obj['id']
    roster = models.ClassRoster.FetchEntity(institution, session, new_class_id)
    self.emails = roster['emails']

  def SpotsAvailable(self):
    if 'open_enrollment' in self.class_obj:
      return self.class_obj['open_enrollment'] - len(self.emails)
    return self.class_obj['max_enrollment'] - len(self.emails)

  def add(self, student_email):
    self.emails.append(student_email)
    self.emails = list(set(self.emails))
    emails = ','.join(self.emails)
    models.ClassRoster.Store(
        self.institution, self.session, self.class_obj, emails)

  def remove(self, student_email):
    self.emails = [ e for e in self.emails if e.lower().strip() != student_email.lower().strip() ]
    emails = ','.join(self.emails)
    models.ClassRoster.Store(
        self.institution, self.session, self.class_obj, emails)


class _ClassInfo(object):
  """Reports on conflicting classes and other class info."""

  def __init__(self, institution, session):
    classes = models.Classes.FetchJson(institution, session)
    self.dayparts_by_class_id = {}
    self.classes_by_id = {}
    for c in classes:
      class_id = str(c['id'])
      self.classes_by_id[class_id] = c
      self.dayparts_by_class_id[class_id] = [s['daypart'] for s in c['schedule']]

  def getClassObj(self, class_id):
    class_obj = self.classes_by_id[class_id]
    if not class_obj:
      logging.fatal('no class_obj')
    if not 'id' in class_obj:
      logging.fatal('class_obj has no id')
    return class_obj

  def RemoveConflicts(self, class_ids, new_class_id):
    """return new_class_id and non-conflicting old class_ids"""
    if new_class_id in class_ids:
      # Check if we are trying to add a class that is already
      # in a student's schedule. (This can happen by running
      # Auto Register multiple times.)
      # If so, don't remove it.
      self.removed_class_ids = []
      return class_ids
    if new_class_id in self.dayparts_by_class_id:
      new_dayparts = self.dayparts_by_class_id[new_class_id]
    else:
      new_dayparts = []
    new_class_ids =  [new_class_id]
    removed_class_ids = []
    for c_id in class_ids:
      if c_id == '':
        continue
      remove = False
      for daypart in self.dayparts_by_class_id[c_id]:
        if daypart in new_dayparts:
          remove = True
      if not remove:
        new_class_ids.append(c_id)
      else:
        removed_class_ids.append(c_id)
    self.removed_class_ids = removed_class_ids
    return new_class_ids


class _StudentSchedule(object):
  """Add and remove classes from student schedule.
  Does not affect class roster."""

  def __init__(self, institution, session, student_email, class_info):
    """Args:
           class_info is a _ClassInfo object
    """
    self.institution = institution
    self.session = session
    self.student_email = student_email
    class_ids = models.Schedule.Fetch(institution, session, student_email)
    self.class_ids = class_ids.split(",")
    self.class_info = class_info

  def add(self, new_class_id):
    class_ids = self.class_ids
    class_ids = self.class_info.RemoveConflicts(class_ids, new_class_id)
    self.class_ids = class_ids
    self.store()

  def remove(self, old_class_id):
    class_ids = self.class_ids
    class_ids = [ i for i in class_ids if i != old_class_id ]
    self.class_ids = class_ids
    self.store()

  def store(self):
    class_ids = ",".join(self.class_ids)
    models.Schedule.Store(
        self.institution, self.session, self.student_email, class_ids)


@ndb.transactional(retries=3, xg=True)
def AddStudentToClass(institution, session, student_email, new_class_id):
  class_info = _ClassInfo(institution, session)
  class_obj = class_info.getClassObj(new_class_id)
  r = _ClassRoster(institution, session, class_obj)
  if r.SpotsAvailable() <= 0:
    return
  r.add(student_email)
  s = _StudentSchedule(institution, session, student_email, class_info)
  s.add(new_class_id)
  for old_class_id in class_info.removed_class_ids:
    class_obj = class_info.getClassObj(old_class_id)
    r = _ClassRoster(institution, session, class_obj)
    r.remove(student_email)


@ndb.transactional(retries=3, xg=True)
def RemoveStudentFromClass(institution, session, student_email, old_class_id):
  class_info = _ClassInfo(institution, session)
  class_obj = class_info.getClassObj(old_class_id)
  r = _ClassRoster(institution, session, class_obj)
  r.remove(student_email)
  s = _StudentSchedule(institution, session, student_email, class_info)
  s.remove(old_class_id)

@ndb.transactional(retries=3, xg=True)
def AddStudentToWaitlist(institution, session, student_email, class_id):
  # No need to check SpotsAvailable or add to StudentSchedule
  # Just make sure student is not already in waitlist
  w = models.ClassWaitlist.FetchEntity(institution, session, class_id)
  if student_email in w['emails']:
    pass
  else:
    w['emails'].append(student_email)
    emails = list(set(w['emails']))
    emails = ','.join(emails)
    models.ClassWaitlist.Store(institution, session, class_id, emails)

@ndb.transactional(retries=3, xg=True)
def RemoveStudentFromWaitlist(institution, session, student_email, class_id):
  w = models.ClassWaitlist.FetchEntity(institution, session, class_id)
  emails = [s for s in w['emails'] if s != student_email]
  emails = ','.join(emails)
  models.ClassWaitlist.Store(institution, session, class_id, emails)


def RunLottery(institution, session, cid, candidates):
  """Modifies roster, waitlist, student groups, and classes
  """
  r = models.ClassRoster.FetchEntity(institution, session, cid)

  # Put people who aren't part of this lottery in the class
  winners = []
  for s in r['emails']:
    if s not in candidates:
      winners.append(s)
  # max_enrollment exceeded just from the non-lottery people!
  # Either admin didn't select enough people or admin allowed
  # open enrollment when there weren't enough spots.
  if len(winners) >= r['max_enrollment']:
    logging.error("Too many non-lottery students; class size exceeds maximum enrollment. Try selecting more students to lottery. Lottery aborted.")
    return

  random.shuffle(candidates)
  # Add lottery candidates into the class until max_enrollment reached
  for c in candidates:
    if len(winners) >= r['max_enrollment']:
      AddStudentToWaitlist(institution, session, c, cid)
      RemoveStudentFromClass(institution, session, c, cid)
    else:
      winners.append(c)

  # put winners into StudentGroup
  group_name = r['class_name'] + '_' + str(r['class_id'])
  sgroup = models.GroupsStudents.FetchJson(institution, session)
  if sgroup:
    if not any(g['group_name'] == group_name for g in sgroup):
      # group_name doesn't exist in StudentGroup
      sgroup.append({'group_name': group_name,
                     'emails': winners})
    else:
      # group_name exists, overwrite existing email list
      for g in sgroup:
        if group_name == g['group_name']:
          g['emails'] = winners
  else:
    # Entire StudentGroup list is empty, create new list
    sgroup = [{'group_name': group_name,
               'emails': winners}]
  sgroup = schemas.StudentGroups().Update(yaml.safe_dump(sgroup, default_flow_style=False))
  models.GroupsStudents.store(institution, session, sgroup)

  class_list = models.Classes.FetchJson(institution, session)
  for c in class_list:
    if c['id'] == int(cid):
      # Don't change the prerequisites since serving rules already
      # restrict student access to the schedule page to those who
      # lost at least one lottery.
      # A lottery winner could drop, in which case we want to allow any
      # lottery loser (who needs to fix their schedule) to add this class.
      #c['prerequisites'] = [{'group':group_name}]

      # Remove open_enrollment field
      result = c.pop('open_enrollment', None)
      if (result == None):
        logging.error("Extra students found while class is not in open enrollment")
      # Update roster class_obj to match above class changes
      r = models.ClassRoster.FetchEntity(institution, session, c['id'])
      models.ClassRoster.Store(institution, session, c, ','.join(r['emails']))
  class_list = schemas.Classes().Update(yaml.safe_dump(class_list, default_flow_style=False))
  models.Classes.store(institution, session, class_list)