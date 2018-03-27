from math import ceil
import os
import signal
import subprocess
from termcolor import colored


PYTHON2 = "python2"
PYTHON3 = "python3"


def alarm_handler(signum, frame):
    raise Exception("Program timed out.")


class Result:

    def __init__(self, grade=None, timed_out=False):
        self.grade = grade
        self.python2_err = None
        self.python3_err = None
        self.timed_out = timed_out
        self.contains_errors = False
        self.reasons = []

    def __errorStr(self):
        if self.contains_errors:
            return "\n\nPython3 Error:\n{p3}\nPython2 Error:\n{p2}".format(
                p3=self.python3_err, p2=self.python2_err)
        else:
            return ""

    def __timedOutStr(self):
        if self.timed_out:
            return "\n\nProgram timed out."
        else:
            return ""

    def __reasonsStr(self):
        if self.reasons:
            return "\n\nIncorrect Results:\n{}".format(
                "\n".join(self.reasons))
        else:
            return ""

    def __str__(self):
        problems = (self.__errorStr()
                    + self.__timedOutStr()
                    + self.__reasonsStr())
        ans = self.grade if problems == "" else "NOT Final Grade"
        base = "Result: {}".format(ans)
        return base + problems

    def setGrade(self, grade):
        self.grade = grade

    def setTimedOut(self, timed_out):
        self.timed_out = timed_out

    def addReason(self, reason):
        self.reasons.append(reason)

    def addReasons(self, reasons):
        self.reasons.extend(reasons)

    def setError(self, err_type, err):
        if err_type == PYTHON2:
            self.python2_err = err
        else:
            self.python3_err = err
        self.contains_errors = True

    def setErrors(self, p2err, p3err):
        self.python2_err = p2err
        self.python3_err = p3err
        self.contains_errors = True


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
                if collection[-1] == "":
                    collection = collection[:-1]
                collections.append(list(collection))
                collection = []
                continue
            collection.append(line.strip())
        if collection[-1] == "":
            collection = collection[:-1]
        collections.append(collection)
        return collections

    def grade(self, user_outputs):
        result = Result()
        score = self.max_score
        for i in range(len(self.outputs)):
            user_output = user_outputs[i]
            expected_output = self.outputs[i]
            scheme = self.schemes[i]
            user_len = len(user_output)
            expected_len = len(expected_output)
            for j in range(min(user_len, expected_len)):
                user_line = user_output[j].strip()
                expected_line = expected_output[j].strip()
                if user_line != expected_line:
                    score -= scheme[j]
                    result.addReason(
                        "User output: {user}\nExpected: {expected}".format(
                            user=user_line, expected=expected_line))
            if user_len < expected_len:
                for i in range(expected_len - user_len + 1, expected_len):
                    score -= scheme[i]
                    result.addReason(
                        "User output does not contain: {}".format(
                            expected_output[i]))
        result.setGrade(score)
        return result


class PythonGrader:

    LATE = colored("LATE", "yellow")
    MISSING = colored("MISSING", "red")
    GRADES = colored("Grades:", "magenta")

    def __init__(self,
                 submissions,
                 rubric,
                 default_grade=0,
                 late_percent=0.05):
        self.submissions = submissions
        self.rubric = rubric
        self.default_grade = default_grade
        self.late_percent = late_percent
        signal.signal(signal.SIGALRM, alarm_handler)

    def __lateness(self, submission):
        if submission.seconds_late > 0:
            days = ceil(submission.seconds_late / 60 / 60 / 24)
            print(submission.user.name, self.LATE,
                  "({} days)".format(days), end=" ")
            max_score = self.rubric.max_score
            max_days = 1 / self.late_percent
            if days >= max_days:
                return max_score
            return max_score * self.late_percent * days
        return 0

    def __evaluateGrade(self, python_ver, submission):
        user_outputs = []
        for test_input in self.rubric.inputs:
            proc = subprocess.Popen(
                [python_ver, submission.filename],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE)
            output, err = None, None
            signal.alarm(15)
            try:
                output, err = proc.communicate(input=test_input)
                signal.alarm(0)
            except Exception as e:
                proc.kill()
                return Result(timed_out=True)
            err_str = err.decode("utf-8")
            if err_str != "":
                proc.kill()
                result = Result()
                result.setError(python_ver, err_str)
                return result
            user_outputs.extend(
                PythonRubric.linesToCollections(
                    output.decode("utf-8").split("\n")))
            proc.kill()
        result = self.rubric.grade(user_outputs) - self.__lateness(submission)
        if result.grade < 0:
            result.setGrade(0)
        return result

    def getResults(self):
        print(self.GRADES)
        results = {}
        for submission in self.submissions:
            user = submission.user
            print(user.name, user.id, end=" ")
            final_result = Result(grade=self.default_grade)
            if submission.exists:
                result = self.__evaluateGrade(PYTHON3, submission)
                if result.timed_out:
                    final_result.setTimedOut(True)
                elif result.contains_errors:
                    python3_err = result.python3_err
                    result = self.__evaluateGrade(PYTHON2, submission)
                    if result.timed_out:
                        final_result.setTimedOut(True)
                    elif result.contains_errors:
                        final_result.setErrors(result.python2_err, python3_err)
                    else:
                        final_result.setGrade(result.grade)
                        final_result.addReasons(result.reasons)
                else:
                    final_result.setGrade(result.grade)
                    final_result.addReasons(result.reasons)
            else:
                print(user.name, self.MISSING, end=" ")
            results[user] = final_result
            print(final_result.grade)
        return results
