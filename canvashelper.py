from canvasapi import Canvas
from datetime import datetime
from difflib import get_close_matches
import config
import json
import os
import requests
import secret
import sys


class CanvasHelper:

    ATTACHMENTS_ATTR = "attachments"
    FILENAME_ATTR = "filename"
    CREATED_AT_ATTR = "created_at"
    URL_ATTR = "url"
    TEMP_FILENAME = "temp.dat"

    class Submission:

        def __init__(self, user, seconds_late):
            self.user = user
            self.seconds_late = seconds_late
            self.path = None
            self.exists = False

        def setPath(self, path):
            self.path = path
            self.exists = True

    def __init__(self, api_token=secret.API_TOKEN):
        cfg = config.get()
        if config.API_URL not in cfg:
            cfg = config.update_api_url(cfg)
        self.api_url = cfg[config.API_URL]
        self.canvas = Canvas(self.api_url, api_token)
        if config.COURSE_IDS not in cfg:
            cfg = config.update_course_ids(cfg, self.canvas)
        self.course_ids = cfg[config.COURSE_IDS]
        self.api_token = api_token
        self.courses = []
        self.assignments = []
        self.selected_course = None
        self.selected_assignment = None

    def __printProgress(self, current_user, total_users):
        sys.stdout.write("\r")
        percent = int((current_user / total_users) * 100)
        sys.stdout.write("({n}/{d}) {p}%".format(
            n=current_user, d=total_users, p=percent))
        sys.stdout.flush()

    def __downloadSubmissionIntoTemp(self, url):
        response = requests.get(url, stream=True)
        with open(self.TEMP_FILENAME, "wb") as temp_file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    temp_file.write(chunk)

    def __getSubmissionDate(self, date_str):
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")

    def __getLatestSubmission(self, attachments):
        if len(attachments) != 1:
            attachments = sorted(
                attachments,
                key=(lambda attachment:
                     self.__getSubmissionDate(
                         attachment[self.CREATED_AT_ATTR])))
        return attachments[0]

    def getSubmissionsDirectory(self):
        return (
            "c" +
            str(self.selected_course.id) + "_" +
            str(self.selected_assignment.id) + "_Submissions")

    def getCourses(self):
        self.courses = [self.canvas.get_course(cid) for cid in self.course_ids]
        return self.courses

    def selectCourse(self, selection):
        self.selected_course = self.courses[selection]

    def getUsers(self):
        return self.selected_course.get_users()

    def getAssignments(self):
        self.assignments = [
            assn for assn in self.selected_course.get_assignments()]
        return self.assignments

    def selectAssignment(self, selection):
        self.selected_assignment = self.assignments[selection]

    def getSelectedAssignment(self):
        return self.selected_assignment

    def getStudentSubset(self):
        subset = set()
        names = [s.name.lower() for s in self.getUsers()]
        query = ":)"
        while query != "":
            query = input("Search Students or [ENTER] to finish: ").lower()
            matches = get_close_matches(query, names, 3, 0.1)
            if not matches:
                print("No near matches. Try Again.")
                continue
            for index in range(3):
                print("[{i}] {n}".format(i=index, n=matches[index]))
            print("[ENTER] None")
            selection = input("selection: ")
            if selection != "":
                subset.add(matches[int(selection)])
        return subset

    def getSubmissions(self):
        submissions = []
        directory_name = self.getSubmissionsDirectory()
        submissions_downloaded = False
        users = {user.id: user for user in self.getUsers()}
        total_users = len(users)
        current_user = 1
        if os.path.exists(directory_name):
            print("Submissions already downloaded.")
            yn = input("Re-download? [Y/n] ").lower()
            if yn != "y":
                submissions_downloaded = True
        else:
            os.makedirs(directory_name)
            init_file = open(directory_name + "/__init__.py", "w")
            init_file.close()
        canvas_submissions = self.selected_assignment.get_submissions()
        for sub in canvas_submissions:
            self.__printProgress(current_user, total_users)
            current_user += 1
            user = users.get(sub.user_id, None)
            if not user:
                continue
            submission = self.Submission(user, int(sub.seconds_late))
            new_filename = directory_name + "/u" + str(user.id) + ".py"
            if self.ATTACHMENTS_ATTR in sub.attributes:
                # Get the last submission attachment download url.
                attachments = [att for att in
                               sub.attributes[self.ATTACHMENTS_ATTR]
                               if att[self.FILENAME_ATTR].endswith(".py")]
                if attachments:
                    latest_submission = self.__getLatestSubmission(attachments)
                    url = latest_submission[self.URL_ATTR]
                    if not submissions_downloaded:
                        self.__downloadSubmissionIntoTemp(url)
                        os.rename(self.TEMP_FILENAME, new_filename)
                    submission.setPath(new_filename)
            submissions.append(submission)
        print()
        return submissions

    def postSubmissionResult(self, user, result, tries=3):
        # Manual request is used instead of canvasapi to verify that grade
        # was uploaded successfully.
        url = (
            self.api_url +
            "api/v1/courses/{}/assignments/{}/submissions/{}".format(
                self.selected_course.id, self.selected_assignment.id, user.id))
        headers = {"Authorization": "Bearer {}".format(self.api_token)}
        payload = {"submission": {"posted_grade": result.grade},
                   "comment": {"text_comment": str(result)}}
        response = requests.put(url, json=payload, headers=headers)
        for i in range(tries - 1):
            if response.status_code == 200:
                return True
            response = requests.put(url, json=payload, headers=headers)
        return False
