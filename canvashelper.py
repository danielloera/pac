import secret
from canvasapi import Canvas
from datetime import datetime
import json
import requests
import os
import wget

default_api_url = "https://utexas.instructure.com/"

# Courses helper will inspect. Must be updated every semester.
default_course_ids = [10170000001214449, 10170000001214450]

class CanvasHelper:

    ATTACHMENTS_ATTR = "attachments"
    FILENAME_ATTR = "filename"
    MODIFIED_AT_ATTR = "modified_at"
    URL_ATTR = "url"

    def __init__(self,
                api_url=default_api_url,
                api_token=secret.API_TOKEN,
                course_ids=default_course_ids):
        self.course_ids = course_ids
        self.canvas = Canvas(api_url, api_token)
        self.api_url = api_url
        self.api_token = api_token
        self.courses = {idx:self.canvas.get_course(course) for idx, course in 
                        zip(range(len(course_ids)), course_ids)}
        self.assignments = {}
        self.selected_course = None
        self.selected_assignment = None

    def __bodyToText__(self, body):
        span_replace = body.replace("<span>", "  ")
        span_replace = span_replace.replace("</span>", "  ")
        pre_replace = span_replace.replace("<pre>", "")
        pre_replace = pre_replace.replace("</pre>", "")
        return pre_replace.replace("<br>", "\n")

    def __getSubmissionDate__(self, attachment):
        return datetime.strptime(attachment[self.MODIFIED_AT_ATTR],
                "%Y-%m-%dT%H:%M:%SZ")

    def __getLatestSubmission__(self, attachments):
        if len(attachments) != 1:
            attachments = sorted(
                attachments,
                key=(lambda attachment:
                        self.__getSubmissionDate__(attachment)))
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
        directory_name = (str(self.selected_course.id) + " " +
                            self.selected_assignment.name + " Submissions")
        if not os.path.exists(directory_name):
            os.makedirs(directory_name)
        else:
            print(
                "Submissions already downloaded. Delete '{}' to redownload."
                .format(directory_name))
            return directory_name
        for sub in self.selected_course.list_submissions(
                self.selected_assignment):
            new_filename = str(sub.user_id) + ".py" 
            if self.ATTACHMENTS_ATTR in sub.attributes:
                # Get the last submission attachment download url.
                attachments = [att for att in sub.attributes[self.ATTACHMENTS_ATTR]
                               if att[self.FILENAME_ATTR].endswith(".py")]
                if not attachments:
                    continue
                latest_submission = self.__getLatestSubmission__(attachments)
                url = latest_submission[self.URL_ATTR]
                # TODO(danielloera) Get date of submission and 
                # find out if it is late.
                raw_filename = wget.download(url)
                os.rename(
                    raw_filename, directory_name + "/" + new_filename)
            elif sub.body is not None:
                text = self.__bodyToText__(sub.body)
                with open(directory_name + "/" + new_filename, "w") as new_file:
                    new_file.write(text)
        return directory_name

    def postSubmissionGrade(self, user, grade, tries=3):
        # Manual request is used instead of canvasapi to verify that grade
        # was uploaded successfully.
        url = (self.api_url + 
            "api/v1/courses/{}/assignments/{}/submissions/{}".format(
            self.selected_course.id, self.selected_assignment.id, user.id))
        headers = {'Authorization': 'Bearer {}'.format(self.api_token)}
        payload = {'submission': {'posted_grade': grade}}
        response = requests.put(url, json=payload, headers=headers)
        for i in range(tries - 1):
            if response.status_code == 200:
                break
            response = requests.put(url, json=payload, headers=headers)
        return response
