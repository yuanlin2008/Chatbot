import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import win32api
import win32con
import tqdm
import database

def init_browser(headless = False):
    """
    初始化browser
    """
    user_data_dir = os.getcwd() + "\\bud"
    b = uc.Chrome(user_data_dir = user_data_dir, headless=headless, version_main=111)
    return b


def cache_dyn_page_js(browser:webdriver.Chrome, update):
    """
    基于js缓存动态下拉网页内容.
    """
    #获取页面高度
    height = browser.execute_script("return action=document.body.scrollHeight")
    #将滚动条调到页面底部
    browser.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    time.sleep(5)
    #定义一个初始时间戳
    t1 = int(time.time())
    num = 0
    while update(browser):
        #获取当前的时间戳
        t2 = int(time.time())
        # 判断时间初始时间戳和当前时间戳相差是否大于30秒，小于30秒则下拉滚动条
        if t2 - t1 < 30:
            new_height = browser.execute_script("return action=document.body.scrollHeight")
            if new_height > height:
                time.sleep(1)
                browser.execute_script('window.scrollTo(0, document.body.scrollHeight)')
                # 重置初始页面高度
                height = new_height
                # 重置初始时间戳，重新计时
                t1 = int(time.time())
        elif num < 3:  # 当超过30秒页面高度仍然没有更新时，进入重试逻辑，重试3次，每次等待20秒
            time.sleep(20)
            num = num + 1
        else:  # 超时并超过重试次数，程序结束跳出循环，并认为页面已经加载完毕！
            print("滚动条已经处于页面最下方！")
            # 滚动条调整至页面顶部
            browser.execute_script('window.scrollTo(0, 0)')
            break

def cache_dyn_page_mouse(browser:webdriver.Chrome, num:int):
    """
    基于mouse event缓存动态下拉网页内容.
    """
    for i in tqdm.trange(num):
        time.sleep(1)
        rect = browser.get_window_rect()
        # 将鼠标移动到窗口位置，触发滚轮事件.
        win32api.SetCursorPos((rect['x']+rect['width']//2, rect['y']+rect['height']//2))
        win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0,0,-500)
    time.sleep(2)


class Wait:
    def __init__(self, browser:webdriver.Chrome) -> None:
        self.wait = WebDriverWait(browser, 10)
    
    def one(self, css_selector:str):
        return self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
    def all(self, css_selector:str):
        return self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector)))


def update_topic_top_qa_links(browser:webdriver.Chrome, topic:str, num:int):
    """
    更新知乎话题精华问答链接列表.
    """
    print(f'开始更新主题问答列表:{topic}...')
    # 搜索话题
    browser.get(f'https://www.zhihu.com/search?q={topic}&type=topic')
    wait = Wait(browser)
    # 选择第一个话题搜索结果.
    topic_link = wait.one('[data-za-detail-view-path-index="0"] .ContentItem-head .ContentItem-title a').get_attribute('href')
    topic_link += '/top-answers'
    browser.get(topic_link)
    cache_dyn_page_mouse(browser, num)

    # 话题名称
    topic_name = wait.one('div.TopicMetaCard-title').get_attribute('textContent')
    # 话题列表.
    topics = browser.find_elements(By.CLASS_NAME, 'List-item.TopicFeedItem')
    valid_num = 0
    new_num = 0
    for topic in topics:
        try:
            ref = topic.find_element(By.XPATH, 'div/div/h2/div/a').get_attribute('href')
        except:
            pass
        else:
            valid_num+=1
            if database.insert_qa(ref):
                new_num+=1
    print(f'话题:{topic_name}({new_num}/{valid_num}/{len(topics)})')

def update_user_qa_links(browser:webdriver.Chrome, user_id:str, max_page:int):
    """
    更新用户问答链接列表.
    """
    print(f'开始更新用户问答列表:{user_id}...')
    wait = Wait(browser)
    # 获得页数
    page_num = 1
    new_num = 0
    browser.get(f'https://www.zhihu.com/people/{user_id}/answers')
    try:
        page_num = int(wait.all('.Pagination > button')[-2].get_attribute('textContent'))
    except:
        page_num = 1
    page_num = min(max_page, page_num) if max_page > 0 else page_num

    for i in tqdm.trange(page_num):
        browser.get(f'https://www.zhihu.com/people/{user_id}/answers?page={i+1}')
        # 问答列表.
        qa_elems = wait.all('.List.Profile-answers .List-item h2 a')
        for qa_elem in qa_elems:
            ref = qa_elem.get_attribute('href')
            if database.insert_qa(ref):
                new_num += 1
    print(f'新增问答{new_num}')

def update_qa(browser:webdriver.Chrome, id:int, url:str):
    """
    更新知乎一个问答数据
    """
    # qa
    browser.get(url)
    wait = Wait(browser)
    # 问题
    question = wait.one('h1.QuestionHeader-title').get_attribute('textContent')
    # 回答
    answer_raw = wait.one('.AnswerCard .css-1g0fqss').get_attribute('innerHTML')
    # 赞同
    vote_str = wait.one('.AnswerCard .Voters > .Button.FEfUrdfMIKpQDJDqkjte.Button--plain.fEPKGkUK5jyc4fUuT0QP').get_attribute('textContent')
    voters = int(vote_str.split()[0].replace(',', ''))
    # 作者
    author = None
    author_id = None
    try:
        author_elem = wait.one('.AnswerAuthor-user-name').find_element(By.CSS_SELECTOR, 'a.UserLink-link')
        author = author_elem.get_attribute('textContent')
        author_id = author_elem.get_attribute('href').split('/')[-1]
    except:
        pass
    # 被收藏.
    collected = 0
    try:
        collected = int(wait.one('.Card[aria-label="更多回答信息"] .Card-header button').get_attribute('textContent'))
    except:
        pass

    # 日期
    datetime = wait.one('.AnswerCard span[aria-label^="发布于"]').get_attribute('textContent')[3:]

    # tags.
    tag_elems = wait.one('.QuestionHeader-tags').find_elements(By.CSS_SELECTOR, 'a div')
    tags = []
    for t in tag_elems:
        tags.append(t.get_attribute('textContent'))
    database.update_qa(id, question, answer_raw, voters, author, author_id, collected, datetime, tags)

def update_all_qa(browser:webdriver.Chrome):
    print(f'开始更新新增问答...')
    for new_qa in tqdm.tqdm(database.select_new_qa()):
        try:
            update_qa(browser, *new_qa)
        except:
            #database.update_qa(new_qa[0])
            pass
    print(f'新增问答更新结束')
