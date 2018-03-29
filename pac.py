from canvashelper import CanvasHelper
from grader import PythonGrader
from grader import Test
import os
from termcolor import colored

GRADING_TERM = "Spring 2018"

OUTPUT_SCHEME_FILE = "output_scheme.txt"
INPUT_FILE = "input.txt"

# Termcolor constants
SUCCESS = colored("SUCCESS", "green")
FAIL = colored("FAIL", "red")
GRADE_UPLOAD_REPORT = colored("Grade Upload Report", "magenta")


def lastname_lex(users):
    return sorted(users, key=lambda user: user.name.split()[1].upper())


def main():
    # Initial information collection
    ch = CanvasHelper()
    print("\nPython Autograder for Canvas")
    print("Grading for {}".format(GRADING_TERM))

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
    pg = PythonGrader(submissions, tests)
    results = pg.getResults(max_score=assignment_points)

    yn = input("\n{} results collected. Upload grades? [y/n] ".format(
        len(results))).lower()


    failed_uploads = []
    failed_grades = []
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
                failed_uploads.append(user)
            if grade == pg.default_grade:
                failed_grades.append(user)

    yn = input("\nShow final report? [y/n] ".format(
        len(results))).lower()

    if yn != "y":
        return

    # Final report for manual grade checking
    print("\nFailed Uploads ({}):".format(len(failed_uploads)))
    for user in lastname_lex(failed_uploads):
        print(user.name, user.id)
    total_failed = len(failed_grades)
    index = 1
    print("\nFailed Grades ({}):\n".format(total_failed))
    for user in lastname_lex(failed_grades):
        print(
            colored("({}/{})".format(index, total_failed), "red"),
            colored(user.name, "white"),
            colored(user.id, "magenta"))
        print(colored(results[user], "white"), "\n")
        index += 1
        input("press [ENTER] for next grade result")


if __name__ == "__main__":
    main()
