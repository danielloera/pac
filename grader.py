import os
import subprocess


class PythonRubric:

    def __init__(self, outputs, schemes, max_score):
        # list of list of expected program lines.
        self.outputs = outputs
        # list of list of grade values of each line
        # corresponding to the output.
        self.schemes = schemes
        self.max_score = max_score

    def grade(self, user_outputs):
        grade = self.max_score
        for i in range(self.outputs):
            user_output = user_output[i]
            expected_output = self.outputs[i]
            scheme = self.schemes[i]
            for j in range(expected_output):
                user_line = user_output[j]
                expected_line = expected_output[j]
                if user_line != expected_line:
                    grade -= scheme[j]
        return grade



class PythonGrader:

    def __init__(self, submissions_dir, users, assignment):
        self.submissions_dir = submissions_dir
        self.users = users 
        self.assignment = assignment
        self.expected_output = "default"
        self.line_count_mode = None
        self.max_lines = 0
        self.args = ""
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
        grade_scheme = {True: str(self.assignment.points_possible),
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
                print(user_str, "has no submission.")
                continue
            proc = self.__createProc__('python3', submission_filename)
            output, err = proc.communicate(input=self.args)
            if err.decode("utf-8") != "":
                proc = self.__createProc__('python2', submission_filename)
                output, err = proc.communicate(input=self.args)
                err = err.decode("utf-8")
                if err != "":
                    grades[user] = self.default_grade
                    print(user_str,
                        "program fails in python3 and python2.\n")
                    continue
            grades[user] = self.__evaluateGrade__(output.decode("utf-8"))
        return grades
