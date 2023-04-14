import sqlite3
import html2text
import tqdm
import typer

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


app = typer.Typer()

@app.command()
def clean():
	"""
	数据清洗
	"""
	global _conn
	global _cursor
	open()
	h2t = html2text.HTML2Text()
	h2t.ignore_links = True
	h2t.ignore_images = True

	rows = _cursor.execute('''
		SELECT id, answer_raw 
		FROM QA 
		WHERE (question IS NOT NULL AND question != "" AND answer IS NULL)
	''').fetchall()
	for row in tqdm.tqdm(rows):
		txt = h2t.handle(row[1])
		_cursor.execute('''
			UPDATE QA
			SET answer = ?
			WHERE id = ?
		''', (txt, row[0]))
		_conn.commit()
	close()

if __name__ == "__main__":
    app()