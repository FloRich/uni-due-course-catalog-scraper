# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class CourseCatalogItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class StudyProgram(scrapy.Item):
    url: scrapy.Field()  # string
    type: scrapy.Field() # string, one of Bachelor, Master
    subjectArea: scrapy.Field() # string,
    categories: scrapy.Field() # Category[]
    comprehensive_subjects: scrapy.Field() # subjects that do not belong in any category

class Category(scrapy.Item):
    url: scrapy.Field() #string
    name: scrapy.Field() # string
    subjects: scrapy.Field() # Subject[]
    categories: scrapy.Field() # Category[]


class Subject(scrapy.Item):
    url: scrapy.Field()  # string
    name: scrapy.Field() # string
    type: scrapy.Field() # one of Vorlesung, Übung, Praktikum, Seminar, Kolloquium, Übung/Praktikum, Tutorium
    shorttext: scrapy.Field() # string
    longttext: scrapy.Field() # string
    sws: scrapy.Field() # number
    semester: scrapy.Field() # string
    persons: scrapy.Field() # Link[]
    timetable:scrapy.Field() # TimeEntry[]
    language: scrapy.Field() # string
    hyperlink: scrapy.Field() # string

class TimeEntry(scrapy.Item):
    day: scrapy.Field() # string
    time: scrapy.Field() # string
    rhythm: scrapy.Field() # string
    room: scrapy.Field() # Link
    comment: scrapy.Field()

class Link(scrapy.Item):
    title: scrapy.Field() # string
    url: scrapy.Field() #string