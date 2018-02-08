from canvashelper import CanvasHelper

grading_term = "Spring 2018"

ch = CanvasHelper()
print("\nPython Autograder for Canvas")
print("Grading for {}".format(grading_term))
ch.showCourseSelection()
course_selection = int(input("\nWhich course would you like to select? "))
ch.selectCourse(course_selection)
ch.showAssignmentSelection()
assn_selection = int(input("\nWhich assignment would you like to select? "))
ch.selectAssignment(assn_selection)
submission_directory = ch.getSubmissions()
users = ch.getUsers()