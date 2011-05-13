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

class NewTest(unittest.TestCase):
# We create our unittest test case
	def __init__(self, testname, rubric_url, rubric_name):
		super(NewTest, self).__init__(testname)

		# Определяем рубрику в яндекс каталоге с которой начать парсить
		if rubric_url != "/":
			self.rubric_url = re.split("http://yaca.yandex.ru/", rubric_url)
			if len(self.rubric_url) < 2:
				print "Bad url must start with http://yaca.yandex.ru/"
				sys.exit()
			self.rubric_url = "/" + self.rubric_url[1]
		else:
			self.rubric_url = rubric_url
		self.rubric_name = rubric_name

	def initRubrics(self):
		if self.rubric_url == "/":
			return

		find_url = "http://yaca.yandex.ru" + self.rubric_url
		cursor = self.db_conn.cursor()
		query_count = "SELECT count(*) FROM rubrics;"
		query = "SELECT * FROM rubrics WHERE url = \"%s\";" % find_url

		cursor.execute(query_count)
		res_count = cursor.fetchone()
		next_id = res_count[0] + 1

		cursor.execute(query)
		res = cursor.fetchone()

		if res:
			found_id = res[0]
			self.parent_id = found_id
			self.shape_id = next_id
			print "We are here"
		else:
			query_replace = "REPLACE INTO rubrics (id, parent_id, name, url) VALUES(%s, %s, \"%s\", \"%s\");" % (next_id, 
																												  0,
																												  self.rubric_name,
																												  find_url)
			cursor.execute(query_replace)
			self.parent_id = next_id
			self.shape_id = next_id + 1

		cursor.close()
	def setUp(self):
		self.verificationErrors = []
		self.loadedUrls = []
		self.shape_id = 1 
		self.parent_id = 0
		self.root_layer = {}
		self.debug_counter = 0
		self.db_conn = MySQLdb.connect(host='localhost', user='qa', passwd='appatit', db='qa_service', charset='utf8')
		
		self.initRubrics()
		# This is an empty array where we will store any verification errors
		# we find in our tests
		self.selenium = selenium("localhost", 4444, "*chrome",	"http://yaca.yandex.ru/")
		self.selenium.start()
		# We instantiate and start the browser

	def createDbShapeRecurse(self, shape, parent_id, layer):
		for key in layer.iterkeys():
			rubric_name = layer[key][0]
			rubric_url = key
			shape[self.shape_id] = [parent_id, rubric_name, rubric_url]
			self.shape_id += 1
			if len(layer[key]) >= 2:
				next_layer = layer[key][1]
				self.createDbShapeRecurse(shape, 
									  self.shape_id - 1,
									  next_layer)
	def createDbShape(self):
		shape = {}
		self.createDbShapeRecurse(shape, self.parent_id, self.root_layer)
		return shape

	def serializeRubrics(self):
		cursor = self.db_conn.cursor()
		db_shape = self.createDbShape() #{"id" : [parent_id, name, url]}
		query = "REPLACE INTO rubrics (id, parent_id, name, url) VALUES"
		for key, val in db_shape.iteritems():
			query += "(%s, %s, \"%s\", \"%s\")," % (key, db_shape[key][0], db_shape[key][1], db_shape[key][2])

		query = query.rstrip(",")
		query += ";"
		print "next query: %s" % query
		try:
			cursor.execute(query)
		except:
			print "Error execute query"
		finally:
		 	cursor.close()

	def createLayer(self, elements, names, delimiter):
		leafs = {}
		rubric_names = names.split(delimiter)
		rubric_names.pop() # remove last "::"

		urls = elements.split(delimiter)
		urls.pop() #remove last "::"

		for i in range(len(urls)):
			leafs[urls[i].lstrip(",")] = [rubric_names[i].lstrip(",")]
		return leafs

	def nextLayer(self, url):
		sel = self.selenium
		time_to_wait = 30000
		counter = 0
		while True:
			try:
				time.sleep(1)
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

		rubrics_on_page = sel.get_eval("var elems = window.document.getElementsByClassName('b-rubric__list__item__link'); var list=[] ;for(var i=0; i < elems.length;i++){list[i] = elems[i] + \"::\"; }; list;")
		rubrics_name = sel.get_eval("var elems = window.document.getElementsByClassName('b-rubric__list__item__link'); var list=[] ;for(var i=0; i < elems.length;i++){list[i] = elems[i].text + \"::\"; }; list;")

		if not rubrics_on_page:
			return None
		rubrics_layer = self.createLayer(rubrics_on_page, rubrics_name, '::')
		return rubrics_layer

	def iterRecurse(self, layer):

		for key, val in layer.iteritems():
			next_layer = self.nextLayer(key)
			if next_layer:
				val.append(next_layer)
				self.iterRecurse(next_layer)

	def test_getrubrics(self):
		# This is the test code.  Here you should put the actions you need
		# the browser to do during your test.

		sel = self.selenium
		# We assign the browser to the variable "sel" (just to save us from
		# typing "self.selenium" each time we want to call the browser).

		self.root_layer = self.nextLayer(self.rubric_url)
		if self.root_layer is None:
			self.fail("Can't create root layer")

		self.iterRecurse(self.root_layer)
		self.serializeRubrics()

	def tearDown(self):
		self.selenium.stop()
		# we close the browser (I'd recommend you to comment this line while
		# you are creating and debugging your tests)

		self.assertEqual([], self.verificationErrors)
		# And make the test fail if we found that any verification errors
		# were found

if __name__ == '__main__':
	import sys
	rubric_url = "/"
	rubric_name = ""
	if len(sys.argv) >= 3:
		rubric_url = sys.argv[1]
		rubric_name = sys.argv[2]

	suite = unittest.TestSuite()
	suite.addTest(NewTest("test_getrubrics", rubric_url, rubric_name))

	unittest.TextTestRunner().run(suite)

