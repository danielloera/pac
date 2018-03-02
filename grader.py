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
        return collections

    def grade(self, user_outputs):
        score = self.max_score
        for i in range(len(self.outputs)):
            user_output = user_outputs[i]
            expected_output = self.outputs[i]
            scheme = self.schemes[i]
            for j in range(len(expected_output)):
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

    def __evaluateGrade__(self, python_ver, submission_filename, if_error=None):
        user_outputs = []
        for test_input in self.rubric.inputs:
            proc = subprocess.Popen(
                [python_ver, '-u', submission_filename],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE)
            output, err = proc.communicate(input=test_input)
            if err.decode("utf-8") != "":
                proc.kill()
                return if_error
            print(output.decode("utf-8").strip().split("\n")+ ["\n"])
            user_outputs.append(
                    PythonRubric.linesToCollections(
                            output.decode("utf-8").split("\n")))
            proc.kill()
        for a in user_outputs:
            print(a)
            print()
        return self.rubric.grade(user_outputs)

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
            score = self.__evaluateGrade__("python3", submission_filename)
            if score is None:
                score = self.__evaluateGrade__("python2", submission_filename,
                        if_error=self.default_grade)
            grades[user] = score
            print(user.name, user.id, score)
        return grades
