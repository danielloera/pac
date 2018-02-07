import secret
from canvasapi import Canvas

default_api_url = "https://utexas.instructure.com"

# Courses helper will inspect. Must be updated every semester.
default_course_ids = [10170000001214449, 10170000001214450]

class CanvasHelper:

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

    def showCourseSelection(self):
        print("\nAvailable Courses:")
        for cidx, course in self.courses.items():
            print(str(cidx) + ":", course.name)

    def selectCourse(self, selection):
        self.selected_course = self.courses[selection]

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

    def getSubmissions(self):
        return self.selected_course.list_submissions(self.selected_assignment)
            
