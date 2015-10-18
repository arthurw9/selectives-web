import models


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


def EligibleClassIdsForStudent(student, classes):
  """Return the set of class ids that the student is eligible to take."""
  class_ids = []
  for c in classes:
    class_id = str(c['id'])
    if not c['prerequisites']:
      class_ids.append(class_id)
    for prereq in c['prerequisites']:
      if 'email' in prereq:
        if student['email'] == prereq['email']:
          class_ids.append(class_id)
      if 'current_grade' in prereq:
        if student['current_grade'] == prereq['current_grade']:
          class_ids.append(class_id)
      if 'group' in prereq:
        #TODO: fix me!
        class_ids.append(class_id)
  return class_ids
