from canvashelper import CanvasHelper
from grader import PythonGrader
from termcolor import colored

grading_term = "Spring 2018"

def main():
    # Initial information gathering
    ch = CanvasHelper()
    print("\nPython Autograder for Canvas")
    print("Grading for {}".format(grading_term))

    ch.showCourseSelection()
    course_selection = int(input("\nWhich course would you like to select? "))
    ch.selectCourse(course_selection)

    ch.showAssignmentSelection()
    assn_selection = int(input("\nWhich assignment would you like to select? "))
    ch.selectAssignment(assn_selection)

    print("Downloading submissions...")
    submission_directory = ch.getSubmissions()
    print()

    users = ch.getUsers()
    assignment = ch.getAssignment()

    # Grading
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

    # Grade uploading
    failed_uploads = []
    failed_grades = []
    for user, grade in grades.items():
        print(user.name, grade, end=" ")
        response = ch.postSubmissionGrade(user, grade)
        if response.status_code == 200:
            print(colored("SUCCESS", "green"))
        else:
            print(colored("FAIL", "red"))
            failed_uploads.append(user)
        if grade == pg.default_grade:
            failed_grades.append(user)

    # Final report for manual grade checking
    print("\nFailed Uploads:")
    for user in failed_uploads:
        print(user.name, user.id)
    print("\nFailed Grades:")
    for user in failed_grades:
        print(user.name, user.id)

if __name__ == '__main__':
    main()
