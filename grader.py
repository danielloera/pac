import json
from math import ceil
import os
import signal
import subprocess
from termcolor import colored


PYTHON2 = "python2"
PYTHON3 = "python3"


def alarm_handler(signum, frame):
    raise Exception("Program timed out.")


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
            return "import {file} as {mod}"
        else:
            args = ",".join(args)
            return "import {file} as {mod}; {mod}.{fn}({args})".format(
                file="{file}", mod="{mod}", fn=function, args=args)

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

    def __init__(self, submissions, tests, default_grade=0, late_percent=0.05):
        self.submissions = submissions
        self.tests = tests
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
        score = 0
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

    def __runTests(self, python_ver, submission):
        user_outputs = []
        for test in self.tests:
            import_name = submission.filename[:-3].replace("/", ".")
            module_name = "module_{}".format(submission.user.id)
            cmd = test.cmd.format(file=import_name, mod=module_name)
            proc = subprocess.Popen(
                [python_ver, "-c", cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE)
            output, err = None, None
            signal.alarm(15)
            try:
                output, err = proc.communicate(input=test.input)
                signal.alarm(0)
            except Exception as e:
                signal.alarm(0)
                proc.kill()
                return self.Result(timed_out=True)
            if err_str != "":
                proc.kill()
                result = self.Result()
                result.setError(python_ver, err_str)
                return result
            output_lines = output.decode("utf-8").split("\n")
            if output_lines[-1] == "":
                output_lines = output_lines[:-1]
            user_outputs.extend([output_lines])
            proc.kill()
        result = self.__grade(user_outputs) #- self.__lateness(submission)
        return result

    def getResults(self, max_score=100):
        print(self.GRADES)
        results = {}
        for submission in self.submissions:
            user = submission.user
            print(user.name, user.id, end=" ")
            final_result = self.Result(grade=self.default_grade)
            if submission.exists:
                result = self.__runTests(PYTHON3, submission)
                if result.timed_out:
                    final_result.setTimedOut(True)
                elif result.contains_errors:
                    python3_err = result.python3_err
                    result = self.__runTests(PYTHON2, submission)
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
            # Add the (possibly) negative grade from testing
            # to the max score to get the students final_grade
            final_grade = max_score + final_result.grade
            final_grade = final_grade if final_grade >= 0 else 0
            final_result.setGrade(final_grade)
            results[user] = final_result
            print(final_result.grade)
        return results
