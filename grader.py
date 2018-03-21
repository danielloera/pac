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

    @classmethod
    def linesToCollections(cls, lines):
        collections = []
        collection = []
        for line in lines:
            if line == "\n":
                collections.append(list(collection))
                collection = []
                continue
            collection.append(line.strip())
        collections.append(collection)
        return collections

    def grade(self, user_outputs):
        score = self.max_score
        for i in range(len(self.outputs)):
            user_output = user_outputs[i]
            expected_output = self.outputs[i]
            scheme = self.schemes[i]
            user_len = len(user_output)
            for j in range(user_len):
                user_line = user_output[j]
                expected_line = expected_output[j]
                if user_line != expected_line:
                    score -= scheme[j]
            expected_len = len(expected_output)
            if user_len < expected_len:
                for line_value in scheme[-(expected_len - user_len):]:
                    score -= line_value
        return score


class PythonGrader:

    def __init__(self, submissions_dir, users, rubric, default_grade="0"):
        self.submissions_dir = submissions_dir
        self.users = users 
        self.rubric = rubric
        self.default_grade = default_grade

    def __evaluateGrade__(self, python_ver, submission_filename):
        user_outputs = []
        for test_input in self.rubric.inputs:
            proc = subprocess.Popen(
                [python_ver, submission_filename],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE)
            output, err = proc.communicate(input=test_input)
            err_str = err.decode("utf-8")
            if err_str != "":
                proc.kill()
                return err_str, False
            user_outputs.append(
                    PythonRubric.linesToCollections(
                            output.decode("utf-8").split("\n")))
            proc.kill()
        return self.rubric.grade(user_outputs), True

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
            value, successful = self.__evaluateGrade__("python3", submission_filename)
            python3_err = ""
            if not successful:
                python3_err = value
                value, successful = self.__evaluateGrade__("python2", submission_filename)
            if successful:
                grades[user] = tuple([value])
            else:
                grades[user] = (self.default_grade, python3_err, value)
        return grades
