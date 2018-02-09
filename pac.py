from canvashelper import CanvasHelper
from grader import PythonGrader

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
assignment = ch.getAssignment()
pg = PythonGrader(submission_directory, users, assignment)
line_count_grading = int(input("\n0: Output Grading\n1: Line Count Grading\n"))
if line_count_grading:
	count = int(input("Max amount of lines: "))
	pg.setMaxLineCount(count)
else:
	output = input("Enter expected output: ")
	pg.setExpectedOutput(output)
args = input("List arguments for program: ")
pg.setArguments(args)
grades = pg.gradeSubmissions()
for user, grade in grades.items():
	ch.postSubmissionGrade(user, grade)
	break