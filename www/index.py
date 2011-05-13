import cherrypy
import MySQLdb
import re
import pdb
import Stemmer

def connect(thread_index):
	cherrypy.thread_data.db = MySQLdb.connect(host='localhost', user='qa', passwd='appatit', db='qa_service', charset='utf8')

cherrypy.engine.subscribe('start_thread', connect)
cherrypy.tools.encode.encoding = 'utf8'

def textToVec(text, stopWords):
	#get all words
	text = text.strip()
	text = text.lower()
	words = re.compile("[^\w]",flags=re.UNICODE).split(text)
	words = filter(lambda a: a != '' and a != ' ', words)

	#remove stop words
	words = filter(lambda a: a not in stopWords, words)

	#stemming
	stm = Stemmer.Stemmer('russian')
	words = stm.stemWords(words)
	return '::'.join(words)

class QaStartPage:
	@cherrypy.expose
	def index(self):
		c = cherrypy.thread_data.db.cursor() 
		c.execute('select * from texts') 
		res = c.fetchone()

		c.execute('select * from stop_words')
		res1 = c.fetchone()
		c.close() 

		stop_words = res1[1].decode("utf8")
		stop_words = re.compile("[^\w]",flags=re.UNICODE).split(stop_words)
		stop_words = filter(lambda a: a != '' and a != ' ', stop_words)
		
		text = res[2].decode("utf8");
		words = textToVec(text, stop_words)
		return "<html><head><meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\" /></head><body>Hello, you have title: %s body: %s records in your table</body></html>" % ('**'.join(stop_words), words)

cherrypy.quickstart(QaStartPage())
