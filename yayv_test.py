import yayv
import testbase
import yaml

class TestYayvByExample(testbase.TestBase):

  def FailWithMessage(self, s, input_value, expected_result, result):
    info = [
      "input: %s" % input_value,
      "schema: %s" % s.schema,
      "expected: %s" % expected_result,
      "actual: %s" % result,
      "counters: %s" % s.counters,
      "unique_values: %s" % s.unique_values,
      "error_message: %s" % s.ErrorMessage(),
    ]
    self.Fail('\n  '.join(info))

  def Assert(self, s, input_value, expected_result):
    result = s.IsValid(input_value)
    if not expected_result == result:
      self.FailWithMessage(s, input_value, expected_result, result)

  def AssertThrows(self, s, input_value):
    try:
      result = s.IsValid(input_value)
      self.FailWithMessage(s, input_value, "Exception", result)
    except:
      pass

  def testBadSchema(self):
    s = yayv.ByExample("[a, b]")
    self.AssertThrows(s, "[a, b]")

  def testSyntax(self):
    s = yayv.ByExample("OPTIONAL")
    self.Assert(s, "[ a, b", False)
    self.Assert(s, "- a\n- b\nc:d\n", False)
    self.Assert(s, "", True)

  def testValue(self):
    s = yayv.ByExample("OPTIONAL")
    self.Assert(s, "abc", True);
    self.Assert(s, "", True);
    self.Assert(s, "a: b", False);
    self.Assert(s, "[a, b, c]", False);

  def testNumbers(self):
    s = yayv.ByExample("OPTIONAL")
    self.Assert(s, "123", True)
    s = yayv.ByExample("REQUIRED")
    self.Assert(s, "123", True)

  def testRequired(self):
    s = yayv.ByExample("REQUIRED")
    self.Assert(s, "abc", True);
    self.Assert(s, "", False);
    self.Assert(s, "a: b", False);
    self.Assert(s, "[a, b, c]", False);

  def testList(self):
    s = yayv.ByExample("[OPTIONAL]")
    self.Assert(s, "[a, b, c]", True)
    self.Assert(s, "a: b", False)
    self.Assert(s, "[]", True)
    self.Assert(s, "", True)
    self.Assert(s, "[a, a, a]", True)

  def testDict(self):
    s = yayv.ByExample("{ abc: REQUIRED, xyz: OPTIONAL }")
    self.Assert(s, "{abc: Hello, xyz: There}", True)
    self.Assert(s, "{abc: Hello}", True)
    self.Assert(s, "{xyz: Hello}", False)
    self.Assert(s, "{foo: Hello}", False)
    self.Assert(s, "foo", False)
    self.Assert(s, "[a, b, c]", False)

  def testUniq(self):
    s = yayv.ByExample("[{ id: UNIQUE, xyz: OPTIONAL }]")
    self.Assert(s, "[{id: Hello, xyz: There}, {id: There, xyz: Blue}]", True)
    self.Assert(s, "[{id: Hello, xyz: Hello}, {id: There, xyz: Blue}]", True)
    self.Assert(s, "[{id: Hello, xyz: There}, {id: Hello, xyz: Blue}]", False)

  def testUniqList(self):
    s = yayv.ByExample("[ UNIQUE ]")
    self.Assert(s, "[a, a, a]", False)
    self.Assert(s, "[a, b, c]", True)

  def testAutoInc(self):
    s = yayv.ByExample("[ {id: AUTO_INC, name: REQUIRED} ]")
    self.Assert(s, "[name: arthur, name: sarah, name: olga]", True)
    s = yayv.ByExample("[ {id: AUTO_INC, name: REQUIRED} ]")
    self.Assert(s, "[{name: arthur, id: 7}, name: sarah, name: olga]", True)
    if s.counters[''] != 7:
      self.FailWithMessage(s, "n/a", "counter starts at 8", s.counters[''])
    self.Assert(s, "[{name: arthur, id: 7}, name: sarah, name: olga]", True)

  def testErrorMessages(self):
    s = yayv.ByExample("{id: AUTO_INC, name: REQUIRED}")
    s.IsValid("first_name: Boo")
    self.AssertEqual("# first_name is not in the schema in ROOT", s.ErrorMessage())
    s = yayv.ByExample("{id: AUTO_INC, name: REQUIRED}")
    s.IsValid("name:")
    self.AssertEqual("# REQUIRED field missing in ROOT.name", s.ErrorMessage())
    s = yayv.ByExample("{id: AUTO_INC, name: REQUIRED}")
    s.IsValid("")
    self.AssertEqual("# Expect yaml_obj to be a dict but it is: None in ROOT", s.ErrorMessage())
    s = yayv.ByExample("- {id: AUTO_INC, name: OPTIONAL}")
    s.IsValid("[ name: arthur, name: olga, names: sarah ]")
    self.AssertEqual("# names is not in the schema in ROOT[2]", s.ErrorMessage())
    s = yayv.ByExample("- {id: AUTO_INC, name: OPTIONAL}")
    s.IsValid("[ name: arthur, name: olga, names: sarah ]")
    self.AssertEqual("# names is not in the schema in ROOT[2]", s.ErrorMessage())
    s = yayv.ByExample("- {id: AUTO_INC, name: OPTIONAL}")
    s.IsValid("[ id: 1, id: 2 ]")
    self.AssertEqual("# ", s.ErrorMessage())
    s = yayv.ByExample("- {id: AUTO_INC, name: OPTIONAL}")
    s.IsValid("[ id: 1, id: 1 ]")
    self.AssertEqual("# duplicate AUTO_INC 1 found in ROOT[1].id", s.ErrorMessage())
    s = yayv.ByExample("- {id1: AUTO_INC 1, id2: AUTO_INC 2, name: UNIQUE a, name2: UNIQUE b}")
    s.IsValid("[ {id1: 1, name: arthur, name2: sarah}, {id2: 1, name: sarah, name2: arthur} ]")
    self.AssertEqual("# ", s.ErrorMessage())
    s = yayv.ByExample("- {name: OPTIONAL, schedule: [ {daypart: UNIQUE 1, room: OPTIONAL} ]}")
    s.IsValid("[ {name: foo, schedule: [ {daypart: monday a, room: 200}, {daypart: tuesday a, room: 200}]}]")
    self.AssertEqual("# ", s.ErrorMessage())
    s = yayv.ByExample("- {name: OPTIONAL, schedule: [ {daypart: UNIQUE 1, room: OPTIONAL} ]}")
    s.IsValid("[ {name: foo, schedule: [ {daypart: monday a, room: 200}, {daypart: monday a, room: 300}]}]")
    self.AssertEqual("# Duplicate Value monday a in UNIQUE 1 in ROOT[0].schedule[1].daypart", s.ErrorMessage())

  def testRealisticIsValidFails(self):
    s = yayv.ByExample(
        "- name: REQUIRED\n"
        "  id: AUTO_INC\n"
        "  instructor: OPTIONAL\n"
        "  max_enrollment: REQUIRED\n"
        "  prerequisites:\n"
        "    - current_grade: OPTIONAL\n"
        "      email: OPTIONAL\n"
        "      group: OPTIONAL\n"
        "  schedule:\n"
        "    - daypart: OPTIONAL\n"
        "      location: OPTIONAL\n")
    s.IsValid(
        "- name: 3D Printing\n"
        "  instructor: Mr. Brown\n"
        "  max_enrollment: 16\n"
        "  prerequisites: []\n"
        "    - current_grade: 8\n"
        "  schedule:\n"
        "    - daypart: Fri A\n"
        "      location: 25\n")
    self.AssertTrue(s.ErrorMessage().startswith("# Traceback"))
    self.AssertTrue("- name: 3D Printing" in s.ErrorMessage())
    self.AssertTrue("- current_grade: 8" in s.ErrorMessage())

  def testRealisticUpdate(self):
    schema = yayv.ByExample(
        "- name: REQUIRED\n"
        "  id: AUTO_INC\n"
        "  instructor: OPTIONAL\n"
        "  max_enrollment: REQUIRED\n"
        "  prerequisites:\n"
        "    - current_grade: OPTIONAL\n"
        "      email: OPTIONAL\n"
        "      group: OPTIONAL\n"
        "  schedule:\n"
        "    - daypart: REQUIRED\n"
        "      location: REQUIRED\n")
    str = schema.Update('\n'.join([
        "- instructor: Mr. McCartney",
        "  max_enrollment: 81",
        "  name: 8th Grade Core",
        "  prerequisites:",
        "  - current_grade: 8",
        "  schedule:",
        "  - daypart: Mon A",
        "    location: Homeroom",
        "  - daypart: Mon B",
        "    location: Homeroom",
        "  - daypart: Thurs A",
        "    location: Homeroom"]))

    # run the unit under test
    actual = schema.Update(str)

    expected = '\n'.join([
        "- id: 1",
        "  instructor: Mr. McCartney",
        "  max_enrollment: 81",
        "  name: 8th Grade Core",
        "  prerequisites:",
        "  - current_grade: 8",
        "  schedule:",
        "  - daypart: Mon A",
        "    location: Homeroom",
        "  - daypart: Mon B",
        "    location: Homeroom",
        "  - daypart: Thurs A",
        "    location: Homeroom",
        ""])
    self.AssertEqual(expected, actual)

  def testAutoIncCounter(self):
    s = yayv.ByExample("- {id: AUTO_INC, name: REQUIRED}")
    n = s.Update("[{name: foo}, {name: bar}]")
    n = yaml.load(n)
    self.AssertEqual({"name": "foo", "id": 1}, n[0])
    self.AssertEqual({"name": "bar", "id": 2}, n[1])

if __name__ == "__main__":
  TestYayvByExample().RunAll()
