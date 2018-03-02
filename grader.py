import os
import subprocess


class PythonRubric:

    def __init__(self, inputs, outputs, schemes, max_score):
        # list of list of inputs to test on.
        self.inputs = inputs
        # list of list of expected program lines.
        self.outputs = outputs
        # list of list of grade values of each line
        # corresponding to the output.
        self.schemes = schemes
        self.max_score = max_score

    def grade(self, user_outputs):
        score = self.max_score
        for i in range(self.outputs):
            user_output = user_output[i]
            expected_output = self.outputs[i]
            scheme = self.schemes[i]
            for j in range(expected_output):
                user_line = user_output[j]
                expected_line = expected_output[j]
                if user_line != expected_line:
                    score -= scheme[j]
        return score


class PythonGrader:

    def __init__(self, submissions_dir, users, rubric, default_grade="0"):
        self.submissions_dir = submissions_dir
        self.users = users 
        self.rubric = rubric
        self.default_grade = default_grade

    def __createProc__(self, python_ver, filename):
        return subprocess.Popen(
            [python_ver, filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE)

    def __evaluateGrade__(self, python_ver):
        pass

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
