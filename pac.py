from canvashelper import CanvasHelper
from difflib import get_close_matches
from grader import PythonGrader
from grader import TestSuite
import os
import util

GRADING_TERM = "Spring 2018"
DEFAULT_TEST_FILE = "testsuite.json"

# Termcolor constants
TITLE = util.colored("Python Autograder for Canvas", "pink")
SUCCESS = util.colored("SUCCESS", "green")
FAIL = util.colored("FAIL", "red")
GRADE_UPLOAD_REPORT = util.colored("Grade Upload Report", "purple")
REPORT_MESSAGE = util.colored(
    "press [ENTER] for next grade result or [q] to skip ", "lightgreen")


def getStudentSelection(all_students):
    option = input("Grade All students [ENTER] or [s]election? ").upper()
    selections = set()
    if option == "S":
        names = [s.name for s in all_students]
        query = ":)"
        while query != "":
            query = input("Search Students or [ENTER] to finish: ")
            matches = get_close_matches(query, names, 3, 0.1)
            if not matches:
                print("No near matches. Try Again.")
                continue
            for index in range(3):
                print("[{i}] {n}".format(i=index, n=matches[index]))
            print("[ENTER] None")
            selection = input("selection: ")
            if selection != "":
                selections.add(matches[int(selection)])
    return selections


def main():
    # Initial information collection
    print(TITLE)
    print("Grading for {}".format(GRADING_TERM))

    ch = CanvasHelper()
    ch.showCourseSelection()
    course_selection = int(input("\nWhich course would you like to select? "))
    ch.selectCourse(course_selection)

    ch.showAssignmentSelection()
    assn_selection = int(
        input("\nWhich assignment would you like to select? "))
    ch.selectAssignment(assn_selection)

    print("Downloading submissions...")
    submissions = ch.getSubmissions()

    # Test Suite Creation
    testsuite = TestSuite.CreateWith(json_file=DEFAULT_TEST_FILE)

    # Grading
    print("Grading...")
    pg = PythonGrader(submissions, testsuite)
    students_to_grade = getStudentSelection(ch.getUsers())
    pg.limitStudentsTo(students_to_grade)
    results = pg.getResults()

    yn = input("\nShow final report? [y/n] ".format(
        len(results))).lower()

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

    yn = input("\n{} results collected. Upload grades? [y/n] ".format(
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
