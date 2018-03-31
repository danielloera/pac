from canvashelper import CanvasHelper
from grader import PythonGrader
from grader import Test
import os
from termcolor import colored

GRADING_TERM = "Spring 2018"

# Termcolor constants
TITLE = colored("Python Autograder for Canvas", "magenta")
SUCCESS = colored("SUCCESS", "green")
FAIL = colored("FAIL", "red")
GRADE_UPLOAD_REPORT = colored("Grade Upload Report", "magenta")
REPORT_MESSAGE = colored(
    "press [ENTER] for next grade result or [q] to skip ", "green")


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

    assignment_points = ch.getAssignment().points_possible

    # Test collection

    tests = Test.FromJson()

    # Grading
    print("Grading...")
    pg = PythonGrader(submissions, tests, assignment_points)
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
                colored("({}/{})".format(index, total_report), "red"),
                colored(user.name, "white"),
                colored(user.id, "magenta"))
            print(colored(results[user], "white"), "\n")
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
