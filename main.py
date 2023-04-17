import typer
import html2text

import scraper
import database

app = typer.Typer()

@app.command()
def topic(topic:str, time:int = 60):
    """
    抓取一个主题问答
    """
    database.open()
    b = scraper.init_browser()
    scraper.update_topic_top_qa_links(b, topic, time)
    b.quit()
    database.close()

@app.command()
def user(user_id:str, max_page:int = 0):
    """
    抓取一个用户问答.
    """
    database.open()
    b = scraper.init_browser(True)
    scraper.update_user_qa_links(b, user_id, max_page)
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
def clean():
    """
    数据清洗
    """
    database.open() 
    h2t = html2text.HTML2Text()
    h2t.ignore_links = True
    h2t.ignore_images = True
    database.clean(h2t.handle)
    database.close()

if __name__ == "__main__":
    app()