import secret
from canvasapi import Canvas
import os
import wget

default_api_url = "https://utexas.instructure.com"

# Courses helper will inspect. Must be updated every semester.
default_course_ids = [10170000001214449, 10170000001214450]

class CanvasHelper:

    ATTACHMENTS_ATTR = 'attachments'
    URL_ATTR = 'url'

    def __init__(self,
                api_url=default_api_url,
                api_token=secret.API_TOKEN,
                course_ids=default_course_ids):
        self.course_ids = course_ids
        self.canvas = Canvas(api_url, api_token)
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
        print("Downloading submissions...")
        directory_name = str(self.selected_assignment.name) + " Submissions"
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
                url = sub.attributes[self.ATTACHMENTS_ATTR][-1][self.URL_ATTR]
                raw_filename = wget.download(url)
                os.rename(
                    raw_filename, directory_name + "/" + new_filename)
            elif sub.body is not None:
                text = self.__bodyToText__(sub.body)
                with open(directory_name + "/" + new_filename, "w") as new_file:
                    new_file.write(text)
        print()
        return directory_name