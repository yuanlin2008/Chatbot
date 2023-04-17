import typer
from typing import List
import html2text
import os
import subprocess

import scraper
import database

app = typer.Typer()

@app.command()
def topic(topics:List[str], time:int = 60):
    """
    抓取主题问答
    """
    database.open()
    b = scraper.init_browser()
    for t in topics:
        scraper.update_topic_top_qa_links(b, t, time)
    b.quit()
    database.close()

@app.command()
def user(user_ids:List[str], max_page:int = 0):
    """
    抓取用户问答.
    """
    database.open()
    b = scraper.init_browser(True)
    for u in user_ids:
        scraper.update_user_qa_links(b, u, max_page)
    b.quit()
    database.close()

@app.command()
def update():
    """
    更新当前问答.
    """
    database.open()
    b = scraper.init_browser(True)
    scraper.update_all_qa(b)
    b.quit()
    database.close()

@app.command()
def clean(all:bool = False):
    """
    数据清洗
    """
    database.open() 
    h2t = html2text.HTML2Text()
    h2t.ignore_links = True
    h2t.ignore_images = True
    database.clean(h2t.handle, all)
    database.close()

@app.command()
def update_model():
    """
    从github更新模型
    """
    if os.path.exists('./model'):
        subprocess.run(['git', 'pull'], cwd='./model')
    else:
        os.makedirs('./model')
        subprocess.run(['git', 'clone', 'https://github.com/THUDM/ChatGLM-6B'], cwd='./model')
    os.system('pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118')
    os.system('pip install -r ./model/ChatGLM-6B/requirements.txt')
    
@app.command()
def test():
    subprocess.run(['python', 'cli_demo.py'], cwd='./model/ChatGLM-6B')

if __name__ == "__main__":
    app()