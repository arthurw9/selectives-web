import logic
import testbase
import fake_request_handler
import fake_users
import fake_ndb

class TestLogic(testbase.TestBase):

  def AssertSchedule(self, institution, session, email, *expected_class_ids):
    actual_class_ids = logic.models.Schedule.Fetch(institution, session, email)
    actual_class_ids = actual_class_ids.split(",")
    if actual_class_ids == ['']:
      actual_class_ids = []
    self.AssertEqual(len(expected_class_ids), len(actual_class_ids),
        "number of class_ids for %s" % email)
    for class_id in expected_class_ids:
      self.AssertTrue(str(class_id) in actual_class_ids,
          "expected class_id %s for %s.\nActual class_ids: %s" %
              (class_id, email, str(actual_class_ids)))

  def AssertClassRoster(self, institution, session, class_id, *expected_emails):
    actual_emails = logic.models.ClassRoster.FetchEntity(
        institution, session, class_id)['emails']
    if actual_emails == ['']:
      actual_emails = []
    self.AssertEqual(len(expected_emails), len(actual_emails), "number of students in class")
    for email in expected_emails:
      self.AssertTrue(email in actual_emails, "expected email %s in actual emails %s" %
          (email, str(actual_emails)))
    for email in actual_emails:
      self.AssertTrue(email in expected_emails, ("unexpected email %s in class %s.\n"
          "Expected emails %s") % (email, class_id, str(expected_emails)))

  def MakeClass(self, class_name, class_id, *dayparts):
    return {"name": class_name,
            "id": str(class_id),
            "max_enrollment": 20,
            "prerequisites": [],
            "schedule":
                [ { "daypart": d } for d in dayparts ]}
 
  def testShouldNotAddStudentToFullClass(self):
    class_id = "1"
    class_a = self.MakeClass("Class A", class_id, "Mon")
    # setup the fake model objects
    logic.models.Classes = fake_ndb.FakeClasses([class_a])
    logic.models.ClassRoster = fake_ndb.FakeClassRoster()
    logic.models.Schedule = fake_ndb.FakeSchedule()
    # call the unit under test and fill up the class with students
    institution = 'abc'
    session = 'fall 2015'
    for student_number in range(1,21):
      student_email = "stew_%d@school.edu" % student_number
      logic.AddStudentToClass(institution, session, student_email, class_id)
      actual_emails = logic.models.ClassRoster.FetchEntity(
          institution, session, class_id)['emails']
      self.AssertEqual(student_number, len(actual_emails))
    # verify all the students are there and the class is full
    actual_emails = logic.models.ClassRoster.FetchEntity(
        institution, session, class_id)['emails']
    self.AssertEqual(20, len(actual_emails))
    self.AssertTrue("stew_1@school.edu" in actual_emails)
    self.AssertTrue("stew_20@school.edu" in actual_emails)
    self.AssertSchedule(institution, session, 'stew_1@school.edu', class_id)
    self.AssertSchedule(institution, session, 'stew_20@school.edu', class_id)
    # Now that the class is full try adding another student
    student_email = "too_late@school.edu"
    logic.AddStudentToClass(institution, session, student_email, class_id)
    # verify they didn't get added
    actual_emails = logic.models.ClassRoster.FetchEntity(
        institution, session, class_id)['emails']
    self.AssertEqual(20, len(actual_emails))
    self.AssertTrue("too_late@school.edu" not in actual_emails)
    self.AssertSchedule(institution, session, "too_late@school.edu")

  def testAddStudentToClass(self):
    # setup selective classes
    class_a = self.MakeClass("Class A", 1, "Mon")
    new_class = self.MakeClass("New Class", 2, "Mon", "Tue")
    class_b = self.MakeClass("Class B", 3, "Tue", "Fri")
    class_c = self.MakeClass("Class C", 4, "Wed")

    # setup the fake model objects
    logic.models.Classes = fake_ndb.FakeClasses(
        [class_a, new_class, class_b, class_c])
    logic.models.ClassRoster = fake_ndb.FakeClassRoster()
    logic.models.Schedule = fake_ndb.FakeSchedule()
    # call the unit under test to give a schedule to a couple of students
    institution = 'abc'
    session = 'fall 2015'
    student_email = 'stew@school.edu'
    logic.AddStudentToClass(institution, session, student_email, class_a['id'])
    logic.AddStudentToClass(institution, session, student_email, class_b['id'])
    logic.AddStudentToClass(institution, session, student_email, class_c['id'])

    student_email = 'dent@school.edu'
    logic.AddStudentToClass(institution, session, student_email, class_a['id'])
    logic.AddStudentToClass(institution, session, student_email, class_b['id'])
    logic.AddStudentToClass(institution, session, student_email, class_c['id'])
    # verify the student schedules and class rosters
    self.AssertSchedule(institution, session, 'stew@school.edu', 1, 3, 4)
    self.AssertSchedule(institution, session, 'dent@school.edu', 1, 3, 4)
    self.AssertClassRoster(institution, session, "1",
                           "stew@school.edu", "dent@school.edu")
    self.AssertClassRoster(institution, session, "2")
    self.AssertClassRoster(institution, session, "3",
                           "stew@school.edu", "dent@school.edu")
    self.AssertClassRoster(institution, session, "4",
                           "stew@school.edu", "dent@school.edu")
    # add a new class to one student that conflict prior classes
    # this should replace classes 1 and 3 with class 2
    student_email = 'stew@school.edu'
    logic.AddStudentToClass(institution, session, student_email, new_class['id'])
    # verify the student schedule and class rosters
    self.AssertSchedule(institution, session, 'stew@school.edu', 2, 4)
    self.AssertSchedule(institution, session, 'dent@school.edu', 1, 3, 4)
    self.AssertClassRoster(institution, session, "1",
                           "dent@school.edu")
    self.AssertClassRoster(institution, session, "2", "stew@school.edu")
    self.AssertClassRoster(institution, session, "3",
                           "dent@school.edu")
    self.AssertClassRoster(institution, session, "4",
                           "stew@school.edu", "dent@school.edu")

  def testRemoveOneStudentFromOneClass(self):
    # setup selective classes
    class_a = self.MakeClass("Class A", 1, "Mon")

    # setup the fake model objects
    logic.models.Classes = fake_ndb.FakeClasses(
        [class_a])
    logic.models.ClassRoster = fake_ndb.FakeClassRoster()
    logic.models.Schedule = fake_ndb.FakeSchedule()
    # add a student to a class
    institution = 'abc'
    session = 'fall 2015'
    student_email = 'stew@school.edu'
    logic.AddStudentToClass(institution, session, student_email, class_a['id'])

    # call the unit under test to remove the student from the class
    logic.RemoveStudentFromClass(
        institution, session, 'stew@school.edu', "1")

    # verify the new class roster and student schedule  
    self.AssertSchedule(institution, session, 'stew@school.edu')
    self.AssertClassRoster(institution, session, "1")

  def testRemoveStudentFromClass(self):
    # setup selective classes
    class_a = self.MakeClass("Class A", 1, "Mon")
    class_b = self.MakeClass("Class B", 2, "Tue", "Fri")
    class_c = self.MakeClass("Class C", 3, "Wed")

    # setup the fake model objects
    logic.models.Classes = fake_ndb.FakeClasses(
        [class_a, class_b, class_c])
    logic.models.ClassRoster = fake_ndb.FakeClassRoster()
    logic.models.Schedule = fake_ndb.FakeSchedule()
    # add a schedule to a couple of students
    institution = 'abc'
    session = 'fall 2015'

    student_email = 'stew@school.edu'
    logic.AddStudentToClass(institution, session, student_email, class_a['id'])
    logic.AddStudentToClass(institution, session, student_email, class_b['id'])
    logic.AddStudentToClass(institution, session, student_email, class_c['id'])

    student_email = 'dent@school.edu'
    logic.AddStudentToClass(institution, session, student_email, class_a['id'])
    logic.AddStudentToClass(institution, session, student_email, class_b['id'])
    logic.AddStudentToClass(institution, session, student_email, class_c['id'])

    # call the unit under test to remove some students from classes
    logic.RemoveStudentFromClass(
        institution, session, 'stew@school.edu', "1")

    # verify the new class roster and student schedule  
    self.AssertSchedule(institution, session, 'stew@school.edu', 2, 3)
    self.AssertSchedule(institution, session, 'dent@school.edu', 1, 2, 3)
    self.AssertClassRoster(institution, session, "1",
                           "dent@school.edu")
    self.AssertClassRoster(institution, session, "2",
                           "stew@school.edu", "dent@school.edu")
    self.AssertClassRoster(institution, session, "3",
                           "stew@school.edu", "dent@school.edu")

  def SetupClassesAndStudentGroups(self):
    classes = []

    classes.append(self.MakeClass("class open to all", 1, "monday"))

    classes.append(self.MakeClass("class open to email", 2, "monday"))
    classes[-1]['prerequisites'].append({"email": "special1@school.edu"})
    classes[-1]['prerequisites'].append({"email": "special2@school.edu"})
    classes[-1]['prerequisites'].append({"email": "special3@school.edu"})

    classes.append(self.MakeClass("class open to grade", 3, "monday"))
    classes[-1]['prerequisites'].append({"current_grade": 7})
    classes[-1]['prerequisites'].append({"current_grade": 8})

    classes.append(self.MakeClass("class open to group", 4, "monday"))
    classes[-1]['prerequisites'].append({"group": "cyclic"})
    classes[-1]['prerequisites'].append({"group": "the_in_crowd"})

    classes.append(self.MakeClass("open to group with grade", 5, "monday"))
    classes[-1]['prerequisites'].append({"group": "the_in_crowd",
                                         "current_grade": 8})
    logic.models.GroupsStudents = fake_ndb.FakeGroupsStudents([
        {"group_name": "the_in_crowd",
         "emails": ["foo@bar.com",
                    "member@the_in_crowd.org"]}])
    return classes


  def testEligibleClassIdsForStudentByDefault(self):
    classes = self.SetupClassesAndStudentGroups()
    institution = "foo"
    session = "bar"

    student = {"email": "stud@school.com", 
               "current_grade": 6}
    # call the unit under test
    class_ids = logic.EligibleClassIdsForStudent(
        institution, session, student, classes)
    self.AssertEqual(['1'], class_ids)

  def testEligibleClassIdsForStudentByEmail(self):
    classes = self.SetupClassesAndStudentGroups()
    institution = "foo"
    session = "bar"

    student = {"email": "special2@school.edu", 
               "current_grade": 6}
    # call the unit under test
    class_ids = logic.EligibleClassIdsForStudent(
        institution, session, student, classes)
    self.AssertEqual(['1', '2'], class_ids)

  def testEligibleClassIdsForStudentByGrade(self):
    classes = self.SetupClassesAndStudentGroups()
    institution = "foo"
    session = "bar"

    student = {"email": "foo1@bar.edu", 
               "current_grade": 8}
    # call the unit under test
    class_ids = logic.EligibleClassIdsForStudent(
        institution, session, student, classes)
    self.AssertEqual(['1', '3'], class_ids)

  def testEligibleClassIdsForStudentByGroup(self):
    classes = self.SetupClassesAndStudentGroups()
    institution = "foo"
    session = "bar"

    student = {"email": "member@the_in_crowd.org", 
               "current_grade": 6}
    # call the unit under test
    class_ids = logic.EligibleClassIdsForStudent(
        institution, session, student, classes)
    self.AssertEqual(['1', '4'], class_ids)

  def testEligibleClassIdsForStudentByGradeAndGroup(self):
    classes = self.SetupClassesAndStudentGroups()
    institution = "foo"
    session = "bar"

    student = {"email": "member@the_in_crowd.org", 
               "current_grade": 8}
    # call the unit under test
    class_ids = logic.EligibleClassIdsForStudent(
        institution, session, student, classes)
    self.AssertEqual(['1', '3', '4', '5'], class_ids)


if __name__ == "__main__":
  TestLogic().RunAll()

