# -*- coding: utf-8 -*-
from selenium import selenium
import MySQLdb
import pdb
import sys
# This is the driver's import.  You'll use this class for instantiating a
# browser and making it do what you need.

import unittest, time, re
# This are the basic imports added by Selenium-IDE by default.
# You can remove the modules if they are not used in your script.

class SiteListTest(unittest.TestCase):
# We create our unittest test case
	def __init__(self, testname, rubric_url):
		super(SiteListTest, self).__init__(testname)

		# Определяем рубрику в яндекс каталоге с которой начать парсить
		self.rubric_url = re.split("http://yaca.yandex.ru/", rubric_url)
		if len(self.rubric_url) < 2:
			print "Bad url must start with http://yaca.yandex.ru/"
			sys.exit()
		self.rubric_url = "/" + self.rubric_url[1]

	def loadRubrics(self):
		find_url = "http://yaca.yandex.ru" + self.rubric_url
		cursor = self.db_conn.cursor()
		query_find = "SELECT id, parent_id FROM rubrics WHERE url = \"%s\";" % find_url
		cursor.execute(query_find)
		res_find = cursor.fetchone()
		if not res_find:
			print "Can't find rubric with url = %s" % find_url
			sys.exit()
		low_border = res_find[0] # id
		level_number = res_find[1] # parent_id

		query_level = "SELECT id FROM rubrics WHERE parent_id = %s ORDER BY id DESC LIMIT 1;" % low_border
		cursor.execute(query_level)
		res_level = cursor.fetchone()
		query_rubrics = ""
		if res_level:
			high_border = res_level[0]
			query_rubrics = "SELECT * FROM (SELECT * FROM rubrics WHERE parent_id >= %s and parent_id <= %s) t1 WHERE id NOT IN (SELECT parent_id FROM rubrics);" % (low_border, high_border)
		else: # Запись с id = low_border только одна на заданном уровне
			query_rubrics = "SELECT * FROM rubrics WHERE id = %s;" % low_border 

		cursor.execute(query_rubrics)
		res_rubrics = cursor.fetchall()
		if not res_rubrics:
			print "error: Can't get rubrics"
			sys.exit()

		for i in res_rubrics:
			self.rubricList.append([i[0], i[1], i[2], i[3]])  # id parent_id name url
		cursor.close()

	def serializeList(self):
		cursor = self.db_conn.cursor()
		query_insert = "REPLACE INTO site_list (rubric_id, urls) VALUES"

		for i in self.siteList:
			query_insert += "(%s, \"%s\")," % (i[0], i[1])

		query_insert = query_insert.rstrip(',')
		cursor.execute(query_insert)
		cursor.close()

	def setUp(self):
		self.verificationErrors = []
		self.rubricList = []
		self.siteList = []
		self.db_conn = MySQLdb.connect(host='localhost', user='qa', passwd='appatit', db='qa_service', charset='utf8')
		
		self.loadRubrics()

		self.selenium = selenium("localhost", 4444, "*firefox",	"http://yaca.yandex.ru/")
		self.selenium.start()

	def getListForRubric(self, rubric):
		sel = self.selenium
		url = rubric[3]
		id = rubric[0]

		time_to_wait = 30000
		counter = 0
		while True:
			try:
				time.sleep(1) #yandex need this
				sel.open(url)
				sel.wait_for_page_to_load(str(time_to_wait))
				break
			except:
				sel.close()
				time_to_wait *= 2
				counter += 1
				if counter > 5:
					message = "Can't open url=" + url;
					print message
					return None

		# click on next button
		time_to_wait = 30000
		cur_list = [id]
		sites = ""
		while True:
			try:
				time.sleep(1)
				sel.click("//a[@class='b-pager__next']")
				sel.wait_for_page_to_load(str(time_to_wait))
				sites_on_page = sel.get_eval("window.document.getElementsByClassName('b-result__name');")
				sites += sites_on_page
			except:
				break

		if sites:
			cur_list.append(sites)
			return cur_list
		else:
			return None

	def test_getsitelist(self):
		# This is the test code.  Here you should put the actions you need
		# the browser to do during your test.
	
		for i in self.rubricList:
			res = self.getListForRubric(i)
			if res:
				self.siteList.append(res)

		self.serializeList()

	def tearDown(self):
		self.selenium.stop()
		# we close the browser (I'd recommend you to comment this line while
		# you are creating and debugging your tests)

		self.assertEqual([], self.verificationErrors)
		# And make the test fail if we found that any verification errors
		# were found

if __name__ == '__main__':
	import sys
	if len(sys.argv) < 2:
		print "error: You MUST enter rubric url to fetch site list to"
		sys.exit()

	rubric_url = sys.argv[1]
	suite = unittest.TestSuite()
	suite.addTest(SiteListTest("test_getsitelist", rubric_url))

	unittest.TextTestRunner().run(suite)

