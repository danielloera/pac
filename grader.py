import json
from math import ceil
import os
import shutil
import signal
import subprocess
import util


PYTHON2 = "python2"
PYTHON3 = "python3"
PYTHON_VERSIONS = [PYTHON3, PYTHON2]


class TimeoutException(Exception):
    pass


def alarm_handler(signum, frame):
    raise TimeoutException


class TestSuite:

    MAX_SCORE = "max_score"
    TESTS = "tests"
    INPUT = "input"
    OUTPUT = "output"
    SCHEME = "scheme"
    MODULE = "module"
    CODE = "code"
    REQUIREMENTS = "requirements"
    REQ_FILE = "file"
    REQ_RENAME = "rename"

    class Test:

        def __createCmdTemplate(self, module, code):
            if module is None:
                module = "__main__"
            if not code:
                return "import {imp} as {mod}".format(imp="{imp}", mod=module)
            else:
                code = "\n".join(code)
                return "import {imp} as {mod}\n{code}".format(
                    imp="{imp}", mod=module, code=code)

        def __init__(self,
                     test_input,
                     output,
                     scheme,
                     module=None,
                     code=None,
                     requirements=None):
            self.input = "".join([(i + "\n")
                                  for i in test_input]).encode("utf-8")
            self.output = output
            self.scheme = scheme
            self.cmd_template = self.__createCmdTemplate(module, code)
            self.requirements = requirements

        def getCmd(self, path):
            import_name = path[:-3].replace("/", ".")
            return self.cmd_template.format(imp=import_name)

        def hasRequirements(self):
            return not (not self.requirements)

    def __init__(self, max_score, tests):
        self.max_score = max_score
        self.tests = tests

    @classmethod
    def CreateWith(cls, json_file=None):
        main_dict = json.load(open(json_file))
        tests = []
        max_score = main_dict[cls.MAX_SCORE]
        for test_dict in main_dict[cls.TESTS]:
            module = test_dict.get(cls.MODULE, None)
            code = test_dict.get(cls.CODE, None)
            requirements = test_dict.get(cls.REQUIREMENTS, None)
            tests.append(cls.Test(test_dict[cls.INPUT],
                                  test_dict[cls.OUTPUT],
                                  test_dict[cls.SCHEME],
                                  module,
                                  code,
                                  requirements))
        return cls(max_score, tests)

    def addRequirementsFrom(self, test):
        for requirement in test.requirements:
            req_file = requirement[self.REQ_FILE]
            req_rename = requirement.get(self.REQ_RENAME, None)
            req_rename = req_file if req_rename is None else req_rename
            shutil.copy(
                req_file, req_rename)


class PythonGrader:

    LATE = util.colored("LATE", "yellow")
    MISSING = util.colored("MISSING", "red")
    GRADES = util.colored("Grades:", "purple")

    class Result:

        def __init__(self, grade=None,
                     python2_err=None,
                     python3_err=None,
                     timed_out=False,
                     missing=False):
            self.missing = missing
            self.grade = grade
            self.timed_out = timed_out
            self.contains_errors = False
            self.reasons = []
            self.lateness = 0
            self.python2_err = python2_err
            self.python3_err = python3_err
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
            if self.lateness:
                base += " (-{} lateness points)".format(self.lateness)
            if problems != "":
                base += " (NOT FINAL)"
            elif not self.missing and self.lateness == 0:
                # Good student confirmed ;)
                base += " :)"
            return base + problems

        def setGrade(self, grade):
            self.grade = grade

        def setLateness(self, lateness_points):
            self.lateness = lateness_points
            self.grade -= lateness_points
            self.grade = self.grade if self.grade >= 0 else 0

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
                 testsuite,
                 default_grade=0,
                 late_percent=0.05,
                 timeout=15):
        self.submissions = submissions
        self.testsuite = testsuite
        self.default_grade = default_grade
        self.late_percent = late_percent
        self.timeout = timeout
        signal.signal(signal.SIGALRM, alarm_handler)

    def __getLateness(self, submission):
        if submission.seconds_late > 0:
            days = ceil(submission.seconds_late / 60 / 60 / 24)
            print(submission.user.name, self.LATE,
                  "({} days)".format(days), end=" ")
            max_days = 1 / self.late_percent
            if days >= max_days:
                return self.testsuite.max_score
            return self.testsuite.max_score * self.late_percent * days
        return 0

    def __grade(self, user_outputs):
        result = self.Result()
        score = self.testsuite.max_score
        for i in range(len(self.testsuite.tests)):
            test = self.testsuite.tests[i]
            user_output = user_outputs[i]
            expected_output = test.output
            scheme = test.scheme
            user_len = len(user_output)
            expected_len = len(expected_output)
            for j in range(min(user_len, expected_len)):
                user_line = user_output[j].strip()
                expected_line = expected_output[j].strip()
                if user_line != expected_line:
                    score -= scheme[j]
                    result.addReason(
                        "User output-> {user}\nExpected-> {expected}".format(
                            user=user_line, expected=expected_line))
            if user_len < expected_len:
                for i in range(expected_len - user_len + 1, expected_len):
                    score -= scheme[i]
                    result.addReason(
                        "User output does not contain: {}".format(
                            expected_output[i]))
        result.setGrade(score)
        return result

    def __getOutputLines(self, output):
        lines = output.decode("utf-8").split("\n")
        if not lines:
            return lines
        index = 0
        while index < len(lines) and lines[index].strip() == "":
            index += 1
        front_empty = index
        index = len(lines)
        while index >= 0 and lines[index - 1].strip() == "":
            index -= 1
        back_empty = index
        return lines[front_empty:back_empty]

    def __runTests(self, python_ver, submission):
        user_outputs = []
        for test in self.testsuite.tests:
            if test.hasRequirements():
                self.testsuite.addRequirementsFrom(test)
            proc = subprocess.Popen(
                [python_ver, "-c", test.getCmd(submission.path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE)
            output, err = None, None
            signal.alarm(self.timeout)
            try:
                output, err = proc.communicate(input=test.input)
                signal.alarm(0)
            except TimeoutException:
                proc.kill()
                return self.Result(timed_out=True, grade=self.default_grade)
            proc.kill()
            err_str = err.decode("utf-8")
            if err_str != "":
                return self.Result(
                    python2_err=err_str,
                    python3_err=err_str,
                    grade=self.default_grade)
            output_lines = self.__getOutputLines(output)
            user_outputs.extend([output_lines])
        result = self.__grade(user_outputs)
        result.setLateness(self.__getLateness(submission))
        return result

    def __getResult(self, submission):
        result = None
        python3_err = None
        for python_ver in PYTHON_VERSIONS:
            result = self.__runTests(python_ver, submission)
            if result.contains_errors and python3_err is None:
                python3_err = result.python3_err
            elif not result.timed_out and not result.contains_errors:
                return result
        if result.contains_errors:
            result.setErrors(result.python2_err, python3_err)
        return result

    def limitStudentsTo(self, students=None):
        if students is None:
            students = set()
        if students:
            self.submissions = [
                sub for sub in self.submissions if sub.user.name in students]

    def getResults(self):
        print(self.GRADES)
        results = {}
        for submission in self.submissions:
            user = submission.user
            print(user.name, user.id, end=" ")
            final_result = self.Result(grade=self.default_grade, missing=True)
            if submission.exists:
                final_result = self.__getResult(submission)
            else:
                print(user.name, self.MISSING, end=" ")
            results[user] = final_result
            print(final_result.grade)
        return results
