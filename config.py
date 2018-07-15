import json
import os
import util

CONFIG_FILE = 'pac.config'
API_URL = 'api_url'
COURSE_IDS = 'course_ids'


def get():
    if not os.path.isfile(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as config_file:
            config_file.write('{}')
    with open(CONFIG_FILE, 'r') as config_file:
        config = json.load(config_file)
    return config


def update_api_url(current_configs):
    with open(CONFIG_FILE, 'w+') as config_file:
        config_dict = {}
        api_url = input(
            'Enter API url e.g. https://myschool.instructure.com/: ')
        config_dict[API_URL] = api_url
        config_dict.update(current_configs)
        json.dump(config_dict, config_file)
    return config_dict


def update_course_ids(current_configs, canvas):
    with open(CONFIG_FILE, 'w+') as config_file:
        config_dict = {}
        course_ids = []
        courses = canvas.get_courses()
        print('Select courses to grade')
        finished = 'n'
        while finished == 'n':
            courses_available = [c for c in courses if c.id not in course_ids]
            i = util.get_selection(courses_available, 'course')
            course_ids.append(courses_available[i].id)
            finished = input("Finished selecting courses? [y/n] ")
        config_dict[COURSE_IDS] = course_ids
        config_dict.update(current_configs)
        json.dump(config_dict, config_file)
    return config_dict
