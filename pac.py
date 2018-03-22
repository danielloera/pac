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
    outputs.append(output)
    schemes.append(scheme)
    return outputs, schemes

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
        with open(OUTPUT_SCHEME_FILE) as output_scheme_file:
            outputs, schemes = get_output_scheme(output_scheme_file)
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
    inputs = None
    print("Gathering input...")
    if os.path.isfile(INPUT_FILE):
        with open(INPUT_FILE) as input_file:
            inputs = PythonRubric.linesToCollections(
                    input_file.readlines())
            inputs = [("\n".join(i) + "\n").encode("utf-8")
                      for i in inputs]
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
    print("Grading...")
    pg = PythonGrader(submission_directory, users, pr)

    results = pg.getResults()

    print("Showing grades.\n")
    for user, result in results.items():
        print(user.name, user.id, result.grade)

    yn = input("\n{} results collected. Upload grades? [y/n] ".format(
            len(results)))

    if yn != "y":
        return

    # Grade uploading
    failed_uploads = []
    failed_grades = []
    print(colored("Grade Upload Report", "magenta"))
    for user, result in results.items():
        grade = result.grade
        print(user.name, grade, end=" ")
        submission_successful = ch.postSubmissionGrade(user, grade)
        if submission_successful:
            print(colored("SUCCESS", "green"))
        else:
            print(colored("FAIL", "red"))
            failed_uploads.append(user)
        if grade == pg.default_grade:
            failed_grades.append(user)

    # Final report for manual grade checking
    print("\nFailed Uploads ({}):".format(len(failed_uploads)))
    for user in lastname_lex(failed_uploads):
        print(user.name, user.id)
    print("\nFailed Grades ({}):\n".format(len(failed_grades)))
    for user in lastname_lex(failed_grades):
        print(colored(user.name, "white"), colored(user.id, "magenta"))
        print(results[user], "\n")
        input("press [ENTER] for next grade result")

if __name__ == '__main__':
    main()
