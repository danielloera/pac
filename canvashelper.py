import secret
from canvasapi import Canvas

API_URL = "https://canvas.instructure.com"

# Courses helper will inspect. Must be updated every semester.
default_course_ids = [10170000001214449, 10170000001214450]

class CanvasHelper:

    def __init__(self,
                api_token=secret.API_TOKEN,
                course_ids=default_course_ids):
        self.course_ids = course_ids
        self.canvas = Canvas(API_URL, secret.API_TOKEN)
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

        # Used solely to retreive the list of assignments.
        # At the moment, course.get_assignments() is not working properly. 
        tempUser = self.selected_course.get_users()[0]

        idx = 0
        for assn in tempUser.get_assignments(self.selected_course):
            self.assignments[idx] = assn
            idx += 1

    def showAssignmentSelection(self):

        self.updateAssignmentSelection()
        print("\nAvailable Assignments:")
        for aidx, assn in self.assignments.items():
            print(str(aidx) + ":", assn.name)


    def selectAssignment(self, selection):
        self.selected_assignment = self.assignments[selection]
