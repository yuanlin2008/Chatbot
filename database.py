import sqlite3

_conn = None
_cursor = None

def open():
	global _conn
	global _cursor
	_conn = sqlite3.connect('data.db')
	_cursor = _conn.cursor()

def close():
	global _conn
	global _cursor
	_cursor.close()
	_conn.close()

def insert_qa(url:str)->bool:
	global _conn
	global _cursor
	try:
		_cursor.execute('insert into QA(url) values(?)', (url,))
		_conn.commit()
		return True
	except:
		return False

def select_new_qa():
	global _conn
	global _cursor
	_cursor.execute('select id, url from QA where question is NULL')
	return _cursor.fetchall()

def _insert_tag(tag):
	global _conn
	global _cursor
	try:
		_cursor.execute('insert into Tag(name) values(?)', (tag,))
		_conn.commit()
		return _cursor.lastrowid
	except:
		_cursor.execute('select id from Tag where name=?', (tag,))
		return _cursor.fetchone()[0]

def update_qa(id, question = "", answer_raw = None, 
	      voters = None, author = None, author_id = None, 
		  collected = None, dt = None, tags = []):
	global _conn
	global _cursor
	qa_tags = []
	for tag in tags:
		qa_tags.append((id, _insert_tag(tag)))
	_cursor.executemany('insert into QATags(qa, tag) values(?, ?)', qa_tags)
	_cursor.execute("update QA set question=?, answer_raw=?, voters=?, author=?, author_id=?, collected=?, datetime=? where id=?", 
							(question, answer_raw, voters, author, author_id, collected, dt, id))
	_conn.commit()
