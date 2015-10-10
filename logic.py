def FindStudent(student_email, students):
  # is students iterable?
  try:
    _ = (e for e in students)
  except TypeError:
    return None
  for student in students:
    if student_email == student['email']:
      return student
  return None

# TODO: Fix me
def EligibleClassesForStudent(student, classes):
  """Return the set of class ids that the student is eligible to take."""
  for c in classes:
    # if c['prerequisites']:
    pass
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
    "      location: REQUIRED\n"

    "- email: UNIQUE\n"
    "  first: REQUIRED\n"
    "  last: REQUIRED\n"
    "  current_grade: REQUIRED\n"
    "  current_homeroom: REQUIRED\n"
