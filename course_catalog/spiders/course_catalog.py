# -*- coding: utf-8 -*-
import scrapy


class CourseCatalogSpider(scrapy.Spider):
    name = 'course-catalog'
    allowed_domains = ['lsf.de']
    start_urls = ['http://lsf.de/']

    def parse(self, response):
        pass

    def extract_studyprograms(self):
        pass

    def extract_categories(self):
        pass

    def extract_subjects(self):
        pass

    def extract_timetable(self):
        pass