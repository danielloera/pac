import os
import subprocess


class PythonGrader:

    def __init__(self, submissions_dir, users, assignment):
        self.submissions_dir = submissions_dir
        self.users = users 
        self.assignment = assignment
        self.expected_output = "default"
        self.line_count_mode = None
        self.max_lines = 0
        self.args = ''
        self.default_grade = "0"

    def setExpectedOutput(self, text):
        self.line_count_mode = False
        self.expected_output = text

    def setMaxLineCount(self, max_lines):
        self.line_count_mode = True
        self.max_lines = max_lines

    def setArguments(self, args):
        self.args = str.encode(args)

    def __createProc__(self, python_ver, filename):
        return subprocess.Popen(
            [python_ver, filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE)

    def __evaluateGrade__(self, output):
        grade_scheme = {True: '100',
                        False: self.default_grade}
        if self.line_count_mode:
            return grade_scheme[len(output.split("\n")) <= self.max_lines]
        else:
            return grade_scheme[output == self.expected_output]

    def gradeSubmissions(self):
        grades = {}
        for user in self.users:
            submission_filename = (self.submissions_dir + "/" + 
                                    str(user.id) + ".py")
            user_str = user.name + "(" + str(user.id) + ")"
            if not os.path.isfile(submission_filename):
                grades[user] = self.default_grade
                print(user_str, "has no submission. Default grade.")
                continue
            proc = self.__createProc__('python2', submission_filename)
            output, err = proc.communicate(input=self.args)
            if err.decode("utf-8") != "":
                proc = self.__createProc__('python3', submission_filename)
                output, err = proc.communicate(input=self.args)
                err = err.decode("utf-8")
                if err != "":
                    grades[user] = self.default_grade
                    print(user_str,
                        "program fails in python2 and python3. Default grade.\n")
                    print("Error:\n", err, "\n")
                    continue
            grades[user] = self.__evaluateGrade__(output.decode("utf-8"))
        return grades
