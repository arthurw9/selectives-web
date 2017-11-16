import webapp2

import index
import welcome
import institution
import dayparts
import classes
import students
import requirements
import verification
import preferences
import impersonation
import scheduler
import groups_classes
import schedule
import groups_students
import class_list
import class_roster
import error_check
import spots_available
import preregistration
import catalog_print
import catalog_full
import catalog_full_print
import logout
import postregistration
import print_schedule
import rosters
import coming_soon
import serving_rules
import auto_register
import report.attendance_list
import report.student_schedules
import report.signup_card
import report.signup_main
import report.signup_pe
import report.homeroom
import report.label
import error_registration
import teachers
import teacher.take_attendance
import teacher.my_rosters
import teacher.all_rosters
import teacher.my_attendance
import teacher.teacher_catalog
import teacher.teacher_roster
import teacher.my_students
import teacher.attendance_today
import teacher.attendance_historical

application = webapp2.WSGIApplication([
  ('/', index.Index),
  ('/welcome', welcome.Welcome),
  ('/institution', institution.Institution),
  ('/dayparts', dayparts.Dayparts),
  ('/classes', classes.Classes),
  ('/students', students.Students),
  ('/requirements', requirements.Requirements),
  ('/verification', verification.Verification),
  ('/preferences', preferences.Preferences),
  ('/schedule', schedule.Schedule),
  ('/impersonation', impersonation.Impersonation),
  ('/scheduler', scheduler.Scheduler),
  ('/groups_classes', groups_classes.GroupsClasses),
  ('/groups_students', groups_students.GroupsStudents),
  ('/class_list', class_list.ClassList),
  ('/class_roster', class_roster.ClassRoster),
  ('/error_check', error_check.ErrorCheck),
  ('/spots_available', spots_available.SpotsAvailable),
  ('/preregistration', preregistration.Preregistration),
  ('/catalog_print', catalog_print.CatalogPrint),
  ('/catalog_full', catalog_full.CatalogFull),
  ('/catalog_full_print', catalog_full_print.CatalogFullPrint),
  ('/logout', logout.LogoutPage),
  ('/postregistration', postregistration.Postregistration),
  ('/print_schedule', print_schedule.PrintSchedule),
  ('/rosters', rosters.Rosters),
  ('/coming_soon', coming_soon.ComingSoon),
  ('/serving_rules', serving_rules.ServingRules),
  ('/auto_register', auto_register.AutoRegister),
  ('/report/attendance_list', report.attendance_list.AttendanceList),
  ('/report/student_schedules', report.student_schedules.StudentSchedules),
  ('/report/signup_card', report.signup_card.SignupCard),
  ('/report/signup_main', report.signup_main.SignupMain),
  ('/report/signup_pe', report.signup_pe.SignupPE),
  ('/report/homeroom', report.homeroom.Homeroom),
  ('/report/label', report.label.Label),
  ('/error_registration', error_registration.ErrorRegistration),
  ('/teachers', teachers.Teachers),
  ('/teacher/take_attendance', teacher.take_attendance.TakeAttendance),
  ('/teacher/my_rosters', teacher.my_rosters.MyRosters),
  ('/teacher/all_rosters', teacher.all_rosters.AllRosters),
  ('/teacher/my_attendance', teacher.my_attendance.MyAttendance),
  ('/teacher/teacher_catalog', teacher.teacher_catalog.TeacherCatalog),
  ('/teacher/teacher_roster', teacher.teacher_roster.TeacherRoster),
  ('/teacher/my_students', teacher.my_students.MyStudents),
  ('/teacher/attendance_today', teacher.attendance_today.AttendanceToday),
  ('/teacher/attendance_historical', teacher.attendance_historical.AttendanceHistorical),
], debug=True)
