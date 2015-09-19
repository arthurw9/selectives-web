"""Base class for unit tests."""

import traceback

class TestBase(object):

  PASS       = "    pass    "
  FAIL       = "*** FAIL ***"
  EXCEPTION  = "** EXCEPT **"

  def RunAll(self):
    num_tests = 0
    num_pass = 0
    status = {}
    for v in dir(self):
      if v.startswith("test"):
        num_tests = num_tests + 1
        self.status = self.PASS
        print "\nStarting Test:", v
        try:
          self.__getattribute__(v)()
          status[v] = self.status
          if status[v] == self.PASS:
            num_pass = num_pass + 1
        except:
          traceback.print_exc()
          status[v] = self.EXCEPTION
    print "\nResults:"
    for t in status:
      print "%13s %s" % (status[t], t)
    print
    print "%d of %d tests passed" % (num_pass, num_tests)
    print

  def Fail(self, msg):
    print msg
    self.status = self.FAIL

  def AssertEqual(self, expected, actual, msg=""):
    if not expected == actual:
      self.Fail("%s\nExpected = %s\nActual = %s\n" % (msg, expected, actual))

  def AssertTrue(self, actual, msg=""):
    if not actual:
      self.Fail("%s\nExpected = True\nActual = False\n" % msg)


# Example Test Class
# Test methods must start with the word test
class TestAddition(TestBase):

  def testOnePlusOneShouldBeTwo(self):
    if not 2 == 1 + 1:
      self.Fail("Addition is broken!")

  def testShouldFail(self):
    self.Fail("This test always fails")

  def testThrowsException(self):
    raise Exception("This test always throws an exception")

  def testOneShouldEqualOne(self):
    self.AssertEqual(1, 1, "One should equal one")

  def testOneShouldEqualTwo(self):
    self.AssertEqual(1, 2, "1 should equal 2 right?.")

  def testTrueIsTrue(self):
    self.AssertTrue(True, "True is true right?")

  def testFalseIsTrue(self):
    self.AssertTrue(False, "False is True right?.")

if __name__ == "__main__":
  TestAddition().RunAll()
