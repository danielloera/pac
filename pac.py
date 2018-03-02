from canvashelper import CanvasHelper
from grader import PythonGrader
from grader import PythonRubric
import os
from termcolor import colored

GRADING_TERM = "Spring 2018"

OUTPUT_SCHEME_FILE = "output_scheme.txt"
INPUT_FILE = "input.txt"

def get_output_scheme(file):
    outputs = []
    schemes = []
    output = []
    scheme = []
    lines = file.readlines()
    i = 0
    while i < len(lines):
        output_line = lines[i]
        if output_line == "\n":
            outputs.append(list(output))
            schemes.append(list(scheme))
            output = []
            scheme = []
            i += 1
            continue
        i += 1
        scheme_line = int(lines[i].strip())
        output.append(output_line.strip())
        scheme.append(scheme_line)
        i += 1
    return outputs, schemes

def get_input(file):
    collections = []
    collection = []
    lines = file.readlines()
    for line in lines:
        if line == "\n":
            collections.append(list(collection))
            collection = []
            continue
        collection.append(line.strip())
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
    print("Gathering output scheme...")
    if os.path.isfile(OUTPUT_SCHEME_FILE):
        outputs, schemes = get_output_scheme(open(OUTPUT_SCHEME_FILE))
    else:
        print(("Please create an output scheme file\n"
               "containing the following format as an example:\n"
               "The next line is how many points this line is worth\n"
               "5"
               "Separate multiple outputs with a newline\n"
               "10"
               "\n"
               "Now begins the second output.\n"
               "10"
               "Always end file with with a newline"
               "75"
               "\n"))
        raise Exception(
                "Expected Output Scheme file {} does not exist.".format(
                        OUTPUT_SCHEME_FILE))
    intputs = None
    print("Gathering input...")
    if os.path.isfile(INPUT_FILE):
        inputs = get_input(open(INPUT_FILE))
    else:
        print(("Please create an input file\n"
               "containing the following format as an example:\n"
               "The next line is how many points this line is worth\n"
               "This is the first input"
               "each line is a new argument"
               "\n"
               "This is the second input"
               "Always end file with a newline"
               "\n"))
        raise Exception(
                "Expected Input file {} does not exist.".format(
                        INPUT_FILE))

    pr = PythonRubric(inputs, outputs, schemes, assignment.points_possible)

    # Grading
    pg = PythonGrader(submission_directory, users, pr)
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
