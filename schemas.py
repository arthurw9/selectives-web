import yayv

dayparts = yayv.ByExample(
    "- name: UNIQUE\n"
    "  row: REQUIRED\n"
    "  col: REQUIRED\n"
    "  rowspan: OPTIONAL\n"
    "  colspan: OPTIONAL\n")

classes = yayv.ByExample(
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
    "  description: OPTIONAL\n"
    "  donation: OPTIONAL\n"
    "  exclude_from_catalog: OPTIONAL\n")

students = yayv.ByExample(
    "- email: UNIQUE\n"
    "  first: REQUIRED\n"
    "  last: REQUIRED\n"
    "  current_grade: REQUIRED\n"
    "  current_homeroom: REQUIRED\n")

requirements = yayv.ByExample(
    "- name: REQUIRED\n"
    "  applies_to:\n"
    "    - current_grade: OPTIONAL\n"
    "      email: OPTIONAL\n"
    "      group: OPTIONAL\n"
    "  id: AUTO_INC\n"
    "  exempt:\n"
    "    - OPTIONAL\n"
    "  class_or_group_options:\n"
    "    - \n"
    "      - OPTIONAL\n")

class_groups = yayv.ByExample(
    "- name: REQUIRED\n"
    "  id: AUTO_INC\n"
    "  classes:\n"
    "    - name: OPTIONAL\n" # for human use
    "      id: REQUIRED\n")

student_groups = yayv.ByExample(
    "- group_name: REQUIRED\n"
    "  emails:\n"
    "    - REQUIRED\n")
