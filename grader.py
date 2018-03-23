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

    class Result:

        def __init__(self):
            self.grade = None
            self.python2_err = None
            self.python3_err = None
            self.contains_errors = False

        def __errorStr(self):
            return "Python3 Error:\n{p3}\nPython2 Error:\n{p2}\n".format(
                p3=self.python3_err, p2=self.python2_err)

        def __str__(self):
            default_str = "Grade: {}".format(self.grade)
            if self.contains_errors:
                return default_str + "\n\n" + self.__errorStr()
            return default_str

        def setGrade(self, grade):
            self.grade = grade

        def setErrors(self, p2err, p3err):
            self.python2_err = p2err
            self.python3_err = p3err
            self.contains_errors = True

    def __init__(self, submissions, rubric, default_grade=0):
        self.submissions = submissions
        self.rubric = rubric
        self.default_grade = default_grade

    def __lateness(self, submission):
        # TODO(danielloera) complete this function
        return 0

    def __evaluateGrade(self, python_ver, submission):
        user_outputs = []
        for test_input in self.rubric.inputs:
            proc = subprocess.Popen(
                [python_ver, submission.filename],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE)
            output, err = proc.communicate(input=test_input)
            err_str = err.decode("utf-8")
            if err_str != "":
                proc.kill()
                return err_str, True
            user_outputs.append(
                PythonRubric.linesToCollections(
                    output.decode("utf-8").split("\n")))
            proc.kill()
        score = self.rubric.grade(user_outputs) - self.__lateness(submission)
        return score, False

    def getResults(self):
        results = {}
        for submission in self.submissions:
            result = self.Result()
            user = submission.user
            user_str = user.name + " (" + str(user.id) + ")"
            if submission.exists:
                value, errors = self.__evaluateGrade("python3", submission)
                python3_err = ""
                if errors:
                    python3_err = value
                    value, errors = self.__evaluateGrade("python2", submission)
                if errors:
                    result.setGrade(self.default_grade)
                    result.setErrors(value, python3_err)
                else:
                    result.setGrade(value)
            else:
                result.setGrade(self.default_grade)
                print(user_str, "has no submission.")
            results[user] = result
        return results
