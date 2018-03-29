import json
from math import ceil
import os
import signal
import subprocess
from termcolor import colored


PYTHON2 = "python2"
PYTHON3 = "python3"
PYTHON_ENVS = [PYTHON3, PYTHON2]

class TimeoutException(Exception):
    pass

def alarm_handler(signum, frame):
    raise TimeoutException


class Test:

    DEFAULT_FILE = "tests.json"
    TESTS = "tests"
    INPUT = "input"
    OUTPUT = "output"
    SCHEME = "scheme"
    FUNCTION = "function"
    ARGS = "args"

    @classmethod
    def FromJson(cls, json_file=DEFAULT_FILE):
        main_dict = json.load(open(json_file))
        tests = []
        for test_dict in main_dict[cls.TESTS]:
            function = None
            args = None
            if cls.FUNCTION in test_dict:
                function = test_dict[cls.FUNCTION]
                args = test_dict[cls.ARGS]
            test = cls(test_dict[cls.INPUT],
                       test_dict[cls.OUTPUT],
                       test_dict[cls.SCHEME],
                       function,
                       args)
            tests.append(test)
        return tests


    def __createCmd(self, function, args):
        if function is None:
            return "import {imp} as {mod}"
        else:
            args = ",".join(args)
            return "import {imp} as {mod}; {mod}.{fn}({args})".format(
                imp="{imp}", mod="{mod}", fn=function, args=args)

    def __init__(self,
                 test_input,
                 output,
                 scheme,
                 function=None,
                 args=None):
        self.input = "".join([(i + "\n")
                              for i in test_input]).encode("utf-8")
        self.output = output
        self.scheme = scheme
        self.cmd = self.__createCmd(function, args)


class PythonGrader:

    LATE = colored("LATE", "yellow")
    MISSING = colored("MISSING", "red")
    GRADES = colored("Grades:", "magenta")

    class Result:

        def __init__(self, grade=None,
                     python2_err=None,
                     python3_err=None,
                     timed_out=False):
            self.grade = grade
            self.timed_out = timed_out
            self.contains_errors = False
            self.reasons = []
            self.python2_err = None
            self.python3_err = None
            self.setErrors(python2_err, python3_err)

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
            base = "Grade: {}".format(self.grade)
            if problems != "":
                base += " (NOT FINAL)"
            else:
                base += " :)"
            return base + problems

        def setGrade(self, grade):
            self.grade = grade

        def setTimedOut(self, timed_out):
            self.timed_out = timed_out

        def addReason(self, reason):
            self.reasons.append(reason)

        def addReasons(self, reasons):
            self.reasons.extend(reasons)

        def setErrors(self, p2err, p3err):
            if p2err is None or p3err is None:
                return
            self.python2_err = p2err
            self.python3_err = p3err
            self.contains_errors = True

    def __init__(self,
                 submissions,
                 tests,
                 max_score,
                 default_grade=0,
                 late_percent=0.05):
        self.submissions = submissions
        self.tests = tests
        self.max_score = max_score
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

    def __grade(self, user_outputs):
        result = self.Result()
        score = self.max_score
        for i in range(len(self.tests)):
            user_output = user_outputs[i]
            expected_output = self.tests[i].output
            scheme = self.tests[i].scheme
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

    def __createProc(self, python_ver, submission, test):
        import_name = submission.filename[:-3].replace("/", ".")
        module_name = "module_{}".format(submission.user.id)
        cmd = test.cmd.format(imp=import_name, mod=module_name)
        return subprocess.Popen(
            [python_ver, "-c", cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE)

    def __runTests(self, submission):
        python3_err = None
        iteration = 0
        for python_ver in PYTHON_ENVS:
            iteration += 1
            user_outputs = []
            for test in self.tests:
                proc = self.__createProc(python_ver, submission, test)
                output, err = None, None
                signal.alarm(15)
                try:
                    output, err = proc.communicate(input=test.input)
                    signal.alarm(0)
                except TimeoutException:
                    proc.kill()
                    if iteration == 1:
                        break
                    return self.Result(timed_out=True, grade=self.default_grade)
                proc.kill()
                err_str = err.decode("utf-8")
                if err_str != "":
                    if iteration == 1:
                        python3_err = err_str
                        break
                    return self.Result(
                        python2_err=err_str,
                        python3_err=python3_err,
                        grade=self.default_grade)
                output_lines = output.decode("utf-8").split("\n")
                if output_lines[-1] == "":
                    output_lines = output_lines[:-1]
                user_outputs.extend([output_lines])
            if user_outputs:
                break
        result = self.__grade(user_outputs)
        grade = result.grade - self.__lateness(submission)
        final_grade = grade if grade >= 0 else 0
        result.setGrade(final_grade)
        return result

    def getResults(self):
        print(self.GRADES)
        results = {}
        for submission in self.submissions:
            user = submission.user
            print(user.name, user.id, end=" ")
            final_result = self.Result(grade=self.default_grade)
            if submission.exists:
                final_result = self.__runTests(submission)
            else:
                print(user.name, self.MISSING, end=" ")
            results[user] = final_result
            print(final_result.grade)
        return results
