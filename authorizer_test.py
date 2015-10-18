import authorizer
import testbase
import fake_request_handler
import fake_users
import fake_ndb
import models

class TestAuthorizer(testbase.TestBase):

  def setupAuthorizer(self, email):
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
    authorizer.users = fake_users.FakeUsers(email)

  def getFakeRequestHandler(self, extra_parameters = {}):
    params = {'institution': 'school_1', 'session': 'fall 2015'}
    params.update(extra_parameters)
    handler = fake_request_handler.RequestHandler(params)
    handler.SetPath("/preferences")
    return handler

  def testShouldSaveRecentAccess(self):
    handler = self.getFakeRequestHandler()
    self.setupAuthorizer("user_123@host")
    auth = authorizer.Authorizer(handler)
    stored_data = authorizer.models.ndb.stored_data
    self.AssertEqual(1, len(stored_data))
    self.AssertEqual(models.RecentAccess, stored_data[0].GetKey()[0])
    self.AssertEqual('user_123@host', stored_data[0].GetKey()[1])

  def testAdminsShouldHaveStudentAccess(self):
    # setup the environment
    handler = self.getFakeRequestHandler({'student': 'stud@school_1'})
    self.setupAuthorizer("admin@host")

    # call the unit under test
    auth = authorizer.Authorizer(handler)
    
    # verify the results
    self.AssertTrue(auth.HasStudentAccess())
    self.AssertEqual("stud@school_1", auth.student_email)

  def testAdminsCantImpersonateNonExistingStudents(self):
    # try to impersonate a student that is not in the student list
    handler = self.getFakeRequestHandler({'student': 'missing_stud@some_other_school'})
    self.setupAuthorizer("admin@host")

    # call the unit under test
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
    self.setupAuthorizer("stud@school_1")
    handler = self.getFakeRequestHandler()

    # call the unit under test
    auth = authorizer.Authorizer(handler)
    
    # verify the results
    self.AssertTrue(auth.HasStudentAccess())
    self.AssertEqual("stud@school_1", auth.student_email)
    
  def testOthersShouldNotHaveStudentAccess(self):
    # try a non-student email
    self.setupAuthorizer("not_a_student@not_the_school")
    handler = self.getFakeRequestHandler()

    # call the unit under test
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

