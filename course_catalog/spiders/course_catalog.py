# -*- coding: utf-8 -*-
import scrapy
import re
from ..items import StudyProgram, Category, Subject, TimeEntry, Person


class CourseCatalogSpider(scrapy.Spider):
    name = 'course-catalog'
    allowed_domains = ['campus.uni-due.de']
    ss19_ingeneurwissenschaften_start_url = "https://campus.uni-due.de/lsf/rds?state=wtree&search=1&trex=step&root120191=225759|219594&P.vx=kurz"
    ws18_19_ingeneurwissenschaften_start_url = "https://campus.uni-due.de/lsf/rds?state=wtree&search=1&trex=step&root120182=215769|207040&P.vx=kurz"
    start_urls = [
        "https://campus.uni-due.de/lsf/rds?state=wtree&search=1&trex=step&root120191=225759|219594&P.vx=kurz",
        "https://campus.uni-due.de/lsf/rds?state=wtree&search=1&trex=step&root120182=215769|207040&P.vx=kurz"
    ]
    table_summary_for_time = "Übersicht über alle Veranstaltungstermine"
    table_summary_for_persons = "Verantwortliche Dozenten"

    def parse(self, response):
        self.log("startig for ss19")
        return self.extract_faculties(response)

    def extract_faculties(self, response):
        width = 60
        links = response.xpath('//a')
        filtered_links = self.filter_links_by_layer(links, '|', 2)
        for link in filtered_links:
            page = response.urljoin(link.attrib['href'])
            request =  scrapy.Request(page, callback=self.extract_studyprograms)
            request.meta['faculty'] = link
            yield request


    def extract_studyprograms(self, response):
        link = response.meta['faculty'].attrib['href']
        number_of_layers = link.count('|')
        studyprograms = []

        links = response.xpath('//a')
        studyprograms_element = self.filter_links_by_layer(links, '|', number_of_layers + 1)

        #extrahiere informations for every strudyprogram
        for studyprogram in studyprograms_element:
            name = str(studyprogram.css('::text').get())
            self.log("extracting" + str(name))
            link = studyprogram.attrib['href']

            type = ""
            if(name.lower().find("master ")>=0):
                type = "Master"
            elif (name.lower().find("bachelor ")>=0):
                type = "Bachelor"

            if type == "":
                self.log("No type for: "+name)
                page = response.urljoin(link)
                request = scrapy.Request(page, callback=self.extract_studyprograms)
                request.meta['faculty'] = studyprogram
                yield request
            else:
                program = StudyProgram(url=link, name=name, program_type=type, categories = [])
                program['id'] = self.extract_category_id(link)
                program['parent_id'] = None
                page = response.urljoin(link)
                request = scrapy.Request(page, callback=self.extract_studyprogram_content)
                request.meta['parent'] = program
                yield request

    def extract_studyprogram_content(self, response):

        #todo: extract courses
        studyprogram = response.meta['parent']
        number_of_layers = studyprogram['url'].count('|')
        links = response.xpath('//a')

        # extract categories
        requests = []
        category_links = self.filter_links_by_layer(links, '|', number_of_layers + 1)
        for category_link in category_links:
            url = category_link.attrib['href']
            name = category_link.css('::text').get()
            id = self.extract_category_id(url)
            category = Category(url = url, name=name, categories = [], id=id, parent_id=studyprogram['id'])
            studyprogram['categories'].append(category['id'])
            page = response.urljoin(url)
            request = scrapy.Request(page, callback=self.extract_categories)
            request.meta['parent'] = category
            yield request
            requests.append(request)

        yield studyprogram

    def extract_categories(self, response):
        parent = response.meta['parent']
        number_of_layers = parent['url'].count('|')
        links = response.xpath("//a")

        # extract categories
        categories = []
        category_links = self.filter_links_by_layer(links, '|', number_of_layers + 1)
        for category_link in category_links:
            url = category_link.attrib['href']
            name = category_link.css('::text').get()
            id = self.extract_category_id(url)
            category = Category(url = url, name=name, categories = [], id=id, parent_id=parent['id'])
            page = response.urljoin(url)
            request = scrapy.Request(page, callback=self.extract_categories)
            request.meta['parent'] = category
            res = yield request
            self.log(res)
            categories.append(category['id'])

        parent['categories'] = categories

        # filter all subjects and add them to the category
        subjects = []
        subject_links = self.filter_links_by_subjects(links)
        for link in subject_links:
            url = link.attrib['href']
            name = link.css('::text').get()
            id = self.extract_subject_id(url)
            subject = Subject(url=url, name=name, id=id, parent_id= parent['id'])
            page = response.urljoin(url)
            request = scrapy.Request(page, callback=self.extract_subject, dont_filter=True)
            request.meta['subject'] = subject
            subjects.append(subject['id'])
            yield request

        parent['subjects'] = subjects

        yield parent

    def extract_subject(self, response):
        subject = response.meta['subject']
        # extract Grunddaten - table
        subject_type = response.xpath("//table[1]//tr[1]/td[1]/text()").get()
        semester = response.xpath("//table[1]//tr[3]/td[1]/text()").get()
        sws = response.xpath("//table[1]//tr[3]/td[2]/text()").get()
        longtext = response.xpath("//table[1]//tr[1]/td[2]/text()").get()
        shorttext = response.xpath("//table[1]//tr[2]/td[2]/text()").get()
        language = response.xpath("//table[1]//tr[8]/td[1]/text()").get()
        hyperlink = response.xpath("//table[1]//tr[7]/td[1]/text()").get()

        # adding table data ot subject
        subject['subject_type'] = subject_type
        subject['semester'] = semester
        subject['sws'] = sws
        subject['longtext'] = longtext
        subject['shorttext'] = shorttext
        subject['language'] = language
        subject['hyperlink'] = hyperlink

        # provide timetable entries and persons
        subject['timetable'] = self.extract_timetable(response)
        subject['persons'] = self.extract_persons(response)

        yield subject

    def extract_timetable(self, response):
        '''
        Extracts all entries from the timetable of a subject
        :param response:
        :return: list of time entries
        '''
        entries = []
        table_xpath = "//table[@summary=\""+ self.table_summary_for_time+"\"]"
        tables = response.xpath(table_xpath)
        for table in tables:
            number_entries = int(float(table.xpath("count(/*/tr)").get()) - 1)
            for index in range(2, 2+number_entries):
                entry_element_str = "/*/tr["+str(index) + "]"
                day = self.clear_string(table.xpath(entry_element_str+"/td[2]/text()").get())
                time = self.clear_string(table.xpath(entry_element_str+"/td[3]/text()").get())
                rhythm = self.clear_string(table.xpath(entry_element_str+"/td[4]/text()").get())
                duration = self.clear_string(table.xpath(entry_element_str+"/td[5]/text()").get())
                room = self.clear_string(table.xpath(entry_element_str+"/td[6]/text()").get())
                status = self.clear_string(table.xpath(entry_element_str+"/td[8]/text()").get())
                comment = self.clear_string(table.xpath(entry_element_str+"/td[9]/text()").get())
                entries.append(TimeEntry(day=day,
                                         time=time,
                                         rhythm=rhythm,
                                         duration = duration,
                                         room = room,
                                         status = status,
                                         comment = comment)
                               )
            return entries

    def extract_persons(self, response):
        '''
        Extracts all listed persons for a subject
        :param response:
        :return: list of persons
        '''
        persons = []
        table_xpath = "//table[@summary=\""+ self.table_summary_for_persons + "\"]"
        number_persons = int(float(response.xpath("count("+table_xpath+"/*/tr)").get()) - 1)

        for index in range(2,2+number_persons):
            self.log(str(index))
            person = response.xpath(table_xpath+"/*/tr["+str(index)+"]/td/a")
            name = self.clear_string(person.css("::text").get())
            url = person.attrib['href']
            persons.append(Person(name=name, url=url))

        return persons


    def filter_links_by_layer(self, links, symbol, count):
        filtered_links = []
        link_elements_without_href = []
        for link in links:
            try:
                href = str(link.attrib['href'])
                if (href.count(symbol) >= count and href.endswith("&P.vx=kurz")):
                    filtered_links.append(link)
            except:
                #self.log('excluded link with no href')
                # do nothing
                link_elements_without_href.append(link)

        #self.log("links without href: " +str(len(link_elements_without_href)))
        return filtered_links

    def filter_links_by_subjects(self, link_elements):
        filtered_links = []
        link_elements_without_href = []
        for link in link_elements:
            try:
                href = str(link.attrib['href'])
                if(href.find("publishSubDir=veranstaltung")>0):
                    filtered_links.append(link)
            except:
                #self.log('excluded link with no href')
                link_elements_without_href.append(link)
                # do nothing

        #self.log("links without href: " + str(len(link_elements_without_href)))
        return filtered_links

    def extract_category_id(self, href):
        return str(href).split('|')[-1].split('&')[0]

    def extract_subject_id(self, href):
        return re.findall(r'\d+', str(href))[0]

    def clear_string(self, string_to_clear):
        return string_to_clear.replace("\t","").replace("\n","").strip(' ')