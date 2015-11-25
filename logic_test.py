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
            "schedule":
                [ { "daypart": d } for d in dayparts ]}
 
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


if __name__ == "__main__":
  TestLogic().RunAll()

