import sqlite3
import tqdm

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
		_cursor.execute('INSERT INTO QA(url) VALUES(?)', (url,))
		_conn.commit()
		return True
	except:
		return False

def select_new_qa():
	global _conn
	global _cursor
	_cursor.execute('''
		SELECT id, url 
		FROM QA 
		WHERE question IS NULL
		''')
	return _cursor.fetchall()

def _insert_tag(tag):
	global _conn
	global _cursor
	try:
		_cursor.execute('INSERT INTO Tag(name) VALUES(?)', (tag,))
		_conn.commit()
		return _cursor.lastrowid
	except:
		_cursor.execute('''
			SELECT id 
			FROM Tag 
			WHERE name=?
			''', (tag,))
		return _cursor.fetchone()[0]

def update_qa(id, question = "", answer_raw = None, 
	      voters = None, author = None, author_id = None, 
		  collected = None, dt = None, tags = []):
	global _conn
	global _cursor
	qa_tags = []
	for tag in tags:
		qa_tags.append((id, _insert_tag(tag)))
	_cursor.executemany('INSERT INTO QATags(qa, tag) VALUES(?, ?)', qa_tags)
	_cursor.execute('''
		UPDATE QA 
		SET question=?, answer_raw=?, voters=?, author=?, author_id=?, collected=?, datetime=? 
		WHERE id=?
		''', (question, answer_raw, voters, author, author_id, collected, dt, id))
	_conn.commit()

def clean(clean_fun, all):
	"""
	数据清洗
	"""
	global _conn
	global _cursor

	# 清理无效的QA.
	_cursor.execute('''
		UPDATE QA
		SET question = ""
		WHERE question IS NULL
	''')
	_conn.commit()

	# answer_raw to answer
	sql = '''
		SELECT id, answer_raw 
		FROM QA 
		WHERE (question IS NOT NULL AND question != "")
	''' if all else '''
		SELECT id, answer_raw 
		FROM QA 
		WHERE (question IS NOT NULL AND question != "" AND answer IS NULL)
	'''
	rows = _cursor.execute(sql).fetchall()
	for row in tqdm.tqdm(rows):
		txt = clean_fun(row[1])
		_cursor.execute('''
			UPDATE QA
			SET answer = ?
			WHERE id = ?
		''', (txt, row[0]))
		_conn.commit()
