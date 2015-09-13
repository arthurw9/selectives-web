"""Base class for unit tests."""

import traceback

class TestBase(object):

  def RunAll(self):
    status = {}
    for v in dir(self):
      if v.startswith("test"):
        self.status = "    pass    "
        print "\nStarting Test:", v
        try:
          self.__getattribute__(v)()
          status[v] = self.status
        except:
          traceback.print_exc()
          status[v] = "** EXCEPT **"
    print "\nResults:"
    print "========"
    for t in status:
      print "%13s %s" % (status[t], t)

  def Fail(self, msg):
    print msg
    self.status = "*** FAIL ***"

  def AssertEqual(self, expected, actual, msg=""):
    if not expected == actual:
      self.Fail("%s\nExpected = %s\nActual = %s\n" % (msg, expected, actual))


# Example Test Class
# Test methods must start with the word test
class TestAddition(TestBase):

  def testOne(self):
    if not 2 == 1 + 1:
      self.Fail("Addition is broken!")

  def testTwo(self):
    self.Fail("This test always fails")

  def testThree(self):
    raise Exception("This test always throws an exception")


if __name__ == "__main__":
  TestAddition().RunAll()
