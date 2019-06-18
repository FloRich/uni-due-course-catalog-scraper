import json
import io
import logging

logging.basicConfig(level=logging.DEBUG)


INPUT_FILE = "../data/output.json"
OUTPUT_FILE = "../data/post_processed_studyprograms.json"

def add_wahl_or_pflicht_to_subjects(category):
    # possible first words
    # Wahlpflichtveranstaltungen
    # Wahlkatalog
    # Wahlpflichtmodule
    # Wahlveranstaltungen, 13
    # Wahlpflichtmodul, 16
    # Wahlpflichtkatalog, 18
    # Modul, 20
    # Wahlplfichtbereich, 252

    # Pflichtfächer, 38
    # Pflichtmodul, 20
    #todo: what is with wahlpflicht?
    if 'subjects' in category:
        words_in_name = category['name'].split(" ")
        first_word = str(words_in_name[0]).lower()
        if first_word.startswith("wahl"):
            category['pflicht'] = 0
        elif first_word.startswith("pflicht"):
            category['pflicht'] = 1


def find_studyprogram_of_category_ids(category_ids, category_dict):
    '''
    For every category it travers up to their studyprogram and returns a list of studyprograms from all categories
    :param category_ids:
    :param category_dict:
    :return:
    '''
    study_programs = set()  #to prevent dublications
    for id in category_ids:
        category = category_dict[id]
        parent_id = category['parent_id']
        while parent_id is not None:
            category = category_dict[parent_id]
            parent_id = category['parent_id']

        study_programs.add(category['name'])

    return list(study_programs)


def fill_dict_for_subjects_and_catagories(data, subjects_dict, categories_dict):
    '''
    Divide between categories and subjects and put them into different dictionaries.
    :param data:
    :param subjects_dict:
    :param categories_dict:
    :return:
    '''
    for entry in data:
        # handle subject differently, because they exists multiple times

        if 'subject_type' in entry:
            if not entry['id'] in subjects_dict:
                # search for all entries of this subject
                subjects_dict[entry['id']] = [entry]
            else:
                subjects_dict[entry['id']].append(entry)

        else:
            categories_dict[entry['id']] = entry

    logging.debug("dictionaries filled")

def convert_multiple_subject_instances_into_one(subjects_dict, categories_dict):
    # merge multiple instance of a subject into one and add all studyprograms to it in which each subject was found
    for id in subjects_dict:
        list_of_subject = subjects_dict[id]
        parent_ids = []
        choosen_subject = list_of_subject[0]
        for subject in list_of_subject:
            parent_ids.append(subject['parent_id'])

        studyprograms = find_studyprogram_of_category_ids(parent_ids, categories_dict)
        choosen_subject['parent_ids'] = parent_ids
        choosen_subject['studyprograms'] = studyprograms
        subjects_dict[choosen_subject['id']] = choosen_subject


def traverse_category_recursivly(category, subjects):
    for subject in category['subjects']:
        subjects.append(subject)

    for cat in category['categories']:
        traverse_category_recursivly(cat, subjects)


def add_stats_about_subject_types_to_studyprogram(studyprogram):
    subject_types_dict = dict()

    subjects = []

    for category in studyprogram['categories']:
        traverse_category_recursivly(category, subjects)

    for subject in subjects:
        if subject['subject_type'] in subject_types_dict:
            subject_types_dict[subject['subject_type']] += 1
        else:
            subject_types_dict[subject['subject_type']] = 1

    studyprogram['stats'] = subject_types_dict


def populate_category(category, subjects_dict, categories_dict):
    # populate categories
    categories = category['categories']
    populated_categories = []
    for category_id in categories:
        populated_categories.append(categories_dict[category_id])

    category['categories'] = populated_categories

    # populate subjects
    if 'subjects' in category:
        subjects = category['subjects']
        populated_subjects = []
        for subject_id in subjects:
            populated_subjects.append(subjects_dict[subject_id])

        category['subjects'] = populated_subjects


#start processing
with io.open(INPUT_FILE, encoding='utf8') as json_file:
    data = json.load(json_file)
    subjects_dict = {}
    categories_dict = {}

    fill_dict_for_subjects_and_catagories(data, subjects_dict, categories_dict)
    convert_multiple_subject_instances_into_one(subjects_dict, categories_dict)


    programs = []
    for id in categories_dict:
        entry = categories_dict[id]

        populate_category(entry, subjects_dict, categories_dict)

        #if it is a studyprogram, add it to the list
        if entry['parent_id'] is None:
            programs.append(entry)
        else:
            #if entry is not a subject, then check if it is of type pflicht or wahl
            if not 'subject_type' in entry:
                add_wahl_or_pflicht_to_subjects(entry)

    #collecting stats for studyprogram
    for studyprogram in programs:
        add_stats_about_subject_types_to_studyprogram(studyprogram)

    with io.open(OUTPUT_FILE, 'w', encoding='utf8') as output_file:
        json.dump(programs,output_file, ensure_ascii=False)
        output_file.close()

    json_file.close()
