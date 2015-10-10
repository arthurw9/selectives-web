import authorizer
import testbase
import fake_request_handler
import fake_users
import fake_ndb
import models

class TestAuthorizer(testbase.TestBase):

  def testShouldSaveRecentAccess(self):
    handler = fake_request_handler.RequestHandler()
    authorizer.users = fake_users.FakeUsers("user@host")
    auth = authorizer.Authorizer(handler)
    stored_data = authorizer.models.ndb.stored_data
    self.AssertEqual(1, len(stored_data))
    self.AssertEqual(models.RecentAccess, stored_data[0].GetKey()[0])
    self.AssertEqual('user@host', stored_data[0].GetKey()[1])

  def testAdminsShouldHaveStudentAccess(self):
    # setup the environment
    handler = fake_request_handler.RequestHandler(
        {'institution': 'school_1',
         'session': 'fall 2015',
         'student': 'stud@school_1'})
    authorizer.users = fake_users.FakeUsers("admin@host")
    authorizer.models.GlobalAdmin = fake_ndb.FakeGlobalAdmin("admin@host")
    authorizer.models.Students = fake_ndb.FakeStudents(
        "[{email: stud@school_1,"
          "first: stud,"
          "last: one,"
          "current_grade: 7,"
          "current_homeroom: 23}]")

    # call the unit under test
    auth = authorizer.Authorizer(handler)
    
    # verify the results
    self.AssertTrue(auth.HasStudentAccess())
    self.AssertEqual("stud@school_1", auth.student_email)

    # try to impersonate a student that is not in the student list
    handler = fake_request_handler.RequestHandler(
        {'institution': 'school_1',
         'session': 'fall 2015',
         'student': 'missing_stud@school_1'})
    auth = authorizer.Authorizer(handler)

    # verify the results
    self.AssertTrue(not auth.HasStudentAccess())
    try:
      self.AssertEqual(not auth.student_email)
      self.Fail("There should be no student_email")
    except AttributeError:
      pass

  def testStudentsShouldHaveStudentAccess(self):
    # setup the environment
    handler = fake_request_handler.RequestHandler(
        {'institution': 'school_1',
         'session': 'fall 2015'})
    handler.SetPath("/preferences")
    authorizer.users = fake_users.FakeUsers("stud@school_1")
    authorizer.models.GlobalAdmin = fake_ndb.FakeGlobalAdmin("admin@host")
    authorizer.models.Admin = fake_ndb.FakeAdmin("admin@host")
    authorizer.models.ServingSession = fake_ndb.FakeServingSession(
        'school_1', 'fall 2015', 'preferences')
    authorizer.models.Students = fake_ndb.FakeStudents(
        "[{email: stud@school_1,"
          "first: stud,"
          "last: one,"
          "current_grade: 7,"
          "current_homeroom: 23}]")

    # call the unit under test
    auth = authorizer.Authorizer(handler)
    
    # verify the results
    print 'blah'
    self.AssertTrue(auth.HasStudentAccess())
    self.AssertEqual("stud@school_1", auth.student_email)
    
    # try a non-student email
    authorizer.users = fake_users.FakeUsers("not_a_student@not_the_school")
    auth = authorizer.Authorizer(handler)
    
    # verify the results
    self.AssertTrue(not auth.HasStudentAccess())
    try:
      self.AssertTrue(not auth.student_email)
      self.Fail("There should be no student_email")
    except AttributeError:
      pass


if __name__ == "__main__":
  TestAuthorizer().RunAll()

