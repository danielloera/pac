from canvashelper import CanvasHelper
from grader import PythonGrader
from grader import PythonRubric
import os
from termcolor import colored

GRADING_TERM = "Spring 2018"

EXPECTED_OUTPUT_FILE = "expected.txt"
SCHEME_FILE = "scheme.txt"

def file_to_collections(file):
    collections = []
    collection = []
    lines = file.readlines()
    for line in lines:
        if line == "\n":
            collections.append(list(collection))
            collection = []
            continue
        collection.append(line.strip())
    collections.append(collection)
    return collections

def main():
    # Initial information collection
    ch = CanvasHelper()
    print("\nPython Autograder for Canvas")
    print("Grading for {}".format(GRADING_TERM))

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

    # Rubric collection
    outputs = None
    schemes = None
    print("Gathering expected outputs...")
    if os.path.isfile(EXPECTED_OUTPUT_FILE):
        outputs = file_to_collections(open(EXPECTED_OUTPUT_FILE))
    else:
        print(("Please create an output file\n"
               "containing the following format as an example:\n"
               "Hello This is my output.\n"
               "This is only the first output.\n"
               "\n"
               "Now begins the second output.\n"
               "Goodbye."))
        raise Exception(
                "Expected Output file {} does not exist.".format(
                        EXPECTED_OUTPUT_FILE))

    print("Gathering schemes...")
    if os.path.isfile(SCHEME_FILE):
        schemes = file_to_collections(open(SCHEME_FILE))
        raise Exception("ss")
    else:
        print(("Please create a scheme file\n"
               "containing the following format as an example:\n"
               "1\n20\n\n15\n44"))
        raise Exception(
                "Expected scheme file {} does not exist.".format(
                        SCHEME_FILE))
    pr = PythonRubric(outputs, schemes, assignment.points_possible)

    # Grading
    pg = PythonGrader(submission_directory, users, assignment, pr)
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
