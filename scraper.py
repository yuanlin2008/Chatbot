import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import win32api
import win32con
import tqdm
import json

def init_browser():
    """
    初始化browser
    """
    user_data_dir = os.getcwd() + "\\bud"
    b = uc.Chrome(user_data_dir = user_data_dir, version_main=111)
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


TOPIC_TOP_LINKS_DIR = "./data/topic_top_links"

def fetch_zhihu_topic_top_links(browser:webdriver.Chrome, topic:str, num:int):
    """
    抓取知乎话题精华链接列表.
    """
    browser.get(f'https://www.zhihu.com/search?q={topic}&type=topic')
    wait = WebDriverWait(browser, 10)
    topic_link = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="SearchMain"]/div/div/div/div/div[2]/div/div/div/div[2]/h2/span/div/a'))).get_attribute('href')
    topic_link += '/top-answers'
    print(topic_link)
    browser.get(topic_link)
    cache_dyn_page_mouse(browser, num)

    if not os.path.exists(TOPIC_TOP_LINKS_DIR):
        os.makedirs(TOPIC_TOP_LINKS_DIR)

    wait = WebDriverWait(browser, 10)
    # 话题名称
    topic_name = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/main/div/div[1]/div[1]/div/div/div[2]/div/div[2]/h2/span/div'))).text
    # 话题列表.
    topics = browser.find_elements(By.CLASS_NAME, 'List-item.TopicFeedItem')
    valid_num = 0
    with open(f'{TOPIC_TOP_LINKS_DIR}/{topic_name}.txt', 'w') as f:
        for topic in topics:
            try:
                ref = topic.find_element(By.XPATH, 'div/div/h2/div/a').get_attribute('href')
            except:
                pass
            else:
                valid_num+=1
                f.write(f'{ref}\n')
    print(f'话题:{topic_name}({valid_num}/{len(topics)})')

def fetch_zhihu_qa(browser:webdriver.Chrome, url:str):
    """
    抓取知乎一个问答
    """
    browser.get(url)
    wait = WebDriverWait(browser, 10)
    qa = {}
    qa['url'] = url
    qa['question_title'] = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.QuestionHeader-title'))).get_attribute('textContent')
    #wait.until(EC.presence_of_element_located((By.XPATH,                        '//*[@id="root"]/div/main/div/div/div[1]/div[2]/div/div[1]/div[1]/div[3]/div/div/div/button'))).click()
    #qa['question_text'] = wait.until(EC.presence_of_element_located((By.XPATH,  '//*[@id="root"]/div/main/div/div/div[1]/div[2]/div/div[1]/div[1]/div[3]/div/div/div/div/span'))).get_attribute('innerHTML')
    qa['answer'] = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.AnswerCard .css-1g0fqss'))).get_attribute('innerHTML')
    vote_str = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.AnswerCard .Voters > .Button.FEfUrdfMIKpQDJDqkjte.Button--plain.fEPKGkUK5jyc4fUuT0QP'))).get_attribute('textContent')
    print(vote_str)
    qa['voters'] = int(vote_str.split()[0].replace(',', ''))

    print(qa)
    return qa

TOPICS = [
    "职场",
    "教育",
    "文化",
]

b = init_browser()
#for t in TOPICS:
    #fetch_zhihu_topic_top_links(b, t, 200)
qa_links = []
for t in TOPICS:
    with open(f'{TOPIC_TOP_LINKS_DIR}/{t}.txt', "r") as f:
        qa_links.extend(f.read().splitlines())
qa = []
for qa_link in tqdm.tqdm(qa_links):
    print(qa_link)
    qa.append(fetch_zhihu_qa(b, qa_link))

with open('./data/qa.txt', 'w') as f:
    json.dumps(qa, f)

b.quit()
