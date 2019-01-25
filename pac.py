from canvashelper import CanvasHelper
from grader import PythonGrader
from grader import TestSuite
import os
import util

DEFAULT_TEST_FILE = "testsuite.json"

# util.colored constants
TITLE = util.colored("Python Autograder for Canvas", "pink")
SUCCESS = util.colored("SUCCESS", "green")
FAIL = util.colored("FAIL", "red")
GRADE_UPLOAD_REPORT = util.colored("Grade Upload Report", "purple")
REPORT_MESSAGE = util.colored(
    "press [ENTER] for next grade result or [q] to skip ", "lightgreen")


def main():
    # Initial information collection
    print(TITLE)

    ch = CanvasHelper()
    course_selection = util.get_selection(ch.getCourses(), "Course")
    ch.selectCourse(course_selection)
    print(util.colored("Grading " + ch.selected_course.name, "lightgreen"))

    assn_selection = util.get_selection(ch.getAssignments(), "Assignment")
    ch.selectAssignment(assn_selection)
    print()

    print("Downloading submissions...")
    submissions = ch.getSubmissions()

    # Test Suite Creation
    testsuite = TestSuite.CreateWith(json_file=DEFAULT_TEST_FILE)

    # Grading
    pg = PythonGrader(submissions, testsuite)
    option = input("Grade All students [ENTER] or [s]election? ").lower()
    if option == "s":
        student_selection = ch.getStudentSubset()
        pg.limitStudentsTo(student_selection)
    results = pg.getResults()

    yn = input("\nShow final report? [y] or [ENTER] to skip ").lower()
    if yn == "y":
        # Final report for manual grade checking
        total_report = len(results)
        index = 1
        print("\nFailed Grades ({}):\n".format(total_report))
        for user in util.lastname_lex(results.keys()):
            print(
                util.colored("({}/{})".format(index, total_report), "red"),
                util.colored(user.name, "white"),
                util.colored(user.id, "purple"))
            print(util.colored(results[user], "white"), "\n")
            index += 1
            q = input(REPORT_MESSAGE)
            print()
            if q == "q":
                break

    yn = input(
        "\n{} results collected. Upload grades? [y] or [ENTER] to skip".format(
            len(results))).lower()
    if yn == "y":
        # Grade uploading
        print(GRADE_UPLOAD_REPORT)
        for user, result in results.items():
            grade = result.grade
            print(user.name, grade, end=" ")
            submission_successful = ch.postSubmissionResult(user, result)
            if submission_successful:
                print(SUCCESS)
            else:
                print(FAIL)


if __name__ == "__main__":
    main()
