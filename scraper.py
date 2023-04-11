from selenium import webdriver
import time
import os

def init_browser():
    # Browser user data dir.
    budDir = os.getcwd() + "\\bud"
    option = webdriver.ChromeOptions()
    option.add_argument(f'user-data-dir={budDir}')
    return webdriver.Chrome(options = option)

def cache_page(browser:webdriver.Chrome, 
               page_url:str):
    browser.get(page_url)
    #获取页面高度
    height = browser.execute_script("return action=document.body.scrollHeight")
    #将滚动条调到页面底部
    browser.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    time.sleep(5)
    #定义一个初始时间戳
    t1 = int(time.time())
    num = 0
    while True:
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