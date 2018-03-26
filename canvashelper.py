import secret
from canvasapi import Canvas
from datetime import datetime
import json
import os
import requests
import wget

default_api_url = "https://utexas.instructure.com/"

# Courses helper will inspect. Must be updated every semester.
default_course_ids = [10170000001214449, 10170000001214450]


class CanvasHelper:

    ATTACHMENTS_ATTR = "attachments"
    FILENAME_ATTR = "filename"
    CREATED_AT_ATTR = "created_at"
    URL_ATTR = "url"

    class Submission:

        def __init__(self, user, seconds_late, filename=None):
            self.user = user
            self.seconds_late = seconds_late
            self.filename = filename
            self.exists = False

        def setFilename(self, filename):
            self.filename = filename
            self.exists = True

    def __init__(self,
                 api_url=default_api_url,
                 api_token=secret.API_TOKEN,
                 course_ids=default_course_ids):
        self.course_ids = course_ids
        self.canvas = Canvas(api_url, api_token)
        self.api_url = api_url
        self.api_token = api_token
        self.courses = {idx: self.canvas.get_course(course) for idx, course in
                        zip(range(len(course_ids)), course_ids)}
        self.assignments = {}
        self.selected_course = None
        self.selected_assignment = None

    def __getSubmissionDate(self, date_str):
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")

    def __getLatestSubmission(self, attachments):
        if len(attachments) != 1:
            attachments = sorted(
                attachments,
                key=(lambda attachment:
                     self.__getSubmissionDate(attachment[CREATED_AT_ATTR])))
        return attachments[0]

    def showCourseSelection(self):
        print("\nAvailable Courses:")
        for cidx, course in self.courses.items():
            print(str(cidx) + ":", course.name)

    def selectCourse(self, selection):
        self.selected_course = self.courses[selection]

    def getUsers(self):
        return self.selected_course.get_users()

    def updateAssignmentSelection(self):
        idx = 0
        for assn in self.selected_course.get_assignments():
            self.assignments[idx] = assn
            idx += 1

    def showAssignmentSelection(self):
        self.updateAssignmentSelection()
        print("\nAvailable Assignments:")
        for aidx, assn in self.assignments.items():
            print(str(aidx) + ":", assn.name)

    def selectAssignment(self, selection):
        self.selected_assignment = self.assignments[selection]

    def getAssignment(self):
        return self.selected_assignment

    def getSubmissions(self):
        submissions = []
        directory_name = (
            str(self.selected_course.id) + " " +
            self.selected_assignment.name + " Submissions")
        submissions_downloaded = False
        users = {user.id: user for user in self.getUsers()}
        if os.path.exists(directory_name):
            print("Submissions already downloaded. Delete '{}' to redownload."
                  .format(directory_name))
            submissions_downloaded = True
        else:
            os.makedirs(directory_name)
        canvas_submissions = self.selected_course.list_submissions(
            self.selected_assignment)
        print("Linking Users...")
        for sub in canvas_submissions:
            user = users[sub.user_id]
            submission = self.Submission(user, int(sub.seconds_late))
            new_filename = directory_name + "/" + str(user.id) + ".py"
            if self.ATTACHMENTS_ATTR in sub.attributes:
                # Get the last submission attachment download url.
                attachments = [att for att in
                               sub.attributes[self.ATTACHMENTS_ATTR]
                               if att[self.FILENAME_ATTR].endswith(".py")]
                if attachments:
                    latest_submission = self.__getLatestSubmission(attachments)
                    url = latest_submission[self.URL_ATTR]
                    if not submissions_downloaded:
                        raw_filename = wget.download(url)
                        os.rename(raw_filename, new_filename)
                    submission.setFilename(new_filename)
            submissions.append(submission)
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
