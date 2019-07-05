CURRENT_SEMESTER = "SoSe 2019"


def create_dict_from_lists(first_list, second_list):
    '''
    Creates one dictionary from two lists. The objects in the list need to have "name" as attribute.
    It will be used as key in the dictionary.
    :param first_list:
    :param second_list:
    :return:
    '''
    dictionary = dict()
    for obj in first_list:
        dictionary[obj['name']] = [obj]
    for obj in second_list:
        if obj['name'] in dictionary:
            objs = dictionary[obj['name']]
            objs.append(obj)
            dictionary[obj['name']] = objs
        else:
            dictionary[obj['name']] = [obj]

    return dictionary


def merge_list_of_categories(categories_dict):
    '''
        Merges all categories that has the same title
        :param categories_dict: a dict with the name of categories as key and a list of subjects as value
        :return: a list of merged categories
        '''
    # merging subcategories
    processed_categories = []
    for category_list in categories_dict.values():
        first_cat = category_list[0]
        if len(category_list) == 2:
            second_cat = category_list[1]
            merged_cat = merge_categories(first_cat, second_cat)
            processed_categories.append(merged_cat)
        else:
            processed_categories.append(first_cat)

    return processed_categories


def merge_list_of_subjects(subjects_dict):
    '''
    Merges all subjects that has the same title
    :param subjects_dict: a dict with the name of the subject as key and a list of subjects as value
    :return: a list of merged subjects
    '''
    # merging subjects
    processed_subjects = []
    for subject_list in subjects_dict.values():
        first_subject = subject_list[0]
        if len(subject_list) == 2:
            second_subject = subject_list[1]
            merged_subject = merge_subjects(first_subject, second_subject)
            processed_subjects.append(merged_subject)
        else:
            processed_subjects.append(first_subject)

    return processed_subjects


def merge_categories(first_category, second_category):
    '''
    Merges two categories into one
    :param first_category: this category will be used as base category
    :param second_category: this category will be merged into the first one
    :return: merges category
    '''
    merged_category = dict()
    merged_category['name'] = first_category['name']
    merged_category['ids'] = [first_category['id'], second_category['id']]
    merged_category['parent_ids'] = [first_category['parent_id'], second_category['parent_id']]
    merged_category['type'] = "category"

    #add all categories by their name to the dict
    categories_dict = create_dict_from_lists(first_category['categories'], second_category['categories'])
    subjects_dict = create_dict_from_lists(first_category['subjects'], second_category['subjects'])

    # merging subcategories
    processed_categories = merge_list_of_categories(categories_dict)

    #merging subjects
    processed_subjects = merge_list_of_subjects(subjects_dict)

    # set categories and subjects of merged category
    merged_category['categories'] = processed_categories
    merged_category['subjects'] = processed_subjects

    return merged_category


def merge_subjects(first_subject, second_subject):
    '''
    Combine two equal subjects into one
    :param first_subject:
    :param second_subject:
    :return:
    '''
    merged_subject = dict()

    if first_subject['semester'] == CURRENT_SEMESTER:
        merged_subject = create_new_subject(first_subject)
    else:
        merged_subject = create_new_subject(second_subject)

    merged_subject['semesters'] = [first_subject['semester'], second_subject['semester']]
    merged_subject['ids'] = [first_subject['id'], second_subject['id']]
    merged_subject['parent_ids'] = [first_subject['parent_id'], second_subject['parent_id']]

    return merged_subject


def create_new_subject(old_subject):
    '''
    Create a new subject and copy all attributes from old one except the semester
    :param old_subject:
    :return:
    '''
    new_subject = dict()

    attribute_list = ['name','url','subject_type', 'shorttext', 'longtext', 'sws', 'persons','timetable','language','hyperlink','studyprograms']
    for attribute in attribute_list:
        new_subject[attribute] = old_subject[attribute]

    return new_subject


def merge_studyprograms(first_studyprogram, second_studyprogram):
    merged_studyprogram = first_studyprogram

    # merging categories
    categories_dict = create_dict_from_lists(first_studyprogram['categories'], second_studyprogram['categories'])
    merged_categories = merge_list_of_categories(categories_dict)
    merged_studyprogram['categories'] = merged_categories

    # merging subjects which are at the root of a studyprogram
    if 'subjects' in first_studyprogram and 'subjects' in second_studyprogram:
        subjects_dict = create_dict_from_lists(first_studyprogram['subjects'], second_studyprogram['subjects'])
        merged_subjects = merge_list_of_subjects(subjects_dict)
        merged_studyprogram['subjects'] = merged_subjects

    return merged_studyprogram
