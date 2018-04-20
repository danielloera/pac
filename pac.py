from canvashelper import CanvasHelper
from grader import PythonGrader
from grader import TestSet
import os
import utils

GRADING_TERM = "Spring 2018"

# Termcolor constants
TITLE = utils.colored("Python Autograder for Canvas", "pink")
SUCCESS = utils.colored("SUCCESS", "green")
FAIL = utils.colored("FAIL", "red")
GRADE_UPLOAD_REPORT = utils.colored("Grade Upload Report", "purple")
REPORT_MESSAGE = utils.colored(
    "press [ENTER] for next grade result or [q] to skip ", "lightgreen")


def lastname_lex(users):
    return sorted(users, key=lambda user: user.name.split()[1].upper())


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

    # Test collection

    testset = TestSet.FromJson()

    # Grading
    print("Grading...")
    pg = PythonGrader(submissions, testset)
    results = pg.getResults()

    yn = input("\nShow final report? [y/n] ".format(
        len(results))).lower()

    if yn == "y":
        # Final report for manual grade checking
        total_report = len(results)
        index = 1
        print("\nFailed Grades ({}):\n".format(total_report))
        for user in lastname_lex(results.keys()):
            print(
                utils.colored("({}/{})".format(index, total_report), "red"),
                utils.colored(user.name, "white"),
                utils. colored(user.id, "purple"))
            print(utils.colored(results[user], "white"), "\n")
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
