from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import re
from pyquery import PyQuery as pq
import pymysql.cursors

conn = pymysql.connect(host='localhost',
                             user='root',
                             password='123456',
                             db='taobao-nianhuo',
                             charset='utf8',
                             cursorclass=pymysql.cursors.DictCursor)
cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)

browser = webdriver.Edge()
wait = WebDriverWait(browser, 10)

def search():
   try:
       browser.get('https://www.taobao.com')
       input = wait.until(
           EC.presence_of_element_located((By.CSS_SELECTOR, '#q'))
       )
       submit = wait.until(
           EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_TSearchForm > div.search-button > button'))
       )
       input.send_keys('年货')
       submit.click()
       total = wait.until(
           EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.total'))
       )
       get_products()
       return total.text
   except TimeoutException:
       return search()

def next_page(page_number):
    try:
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input'))
        )
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit'))
        )
        input.clear()
        input.send_keys(page_number)
        submit.click()
        wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active > span'), str(page_number))
        )
        get_products()
    except TimeoutException:
        next_page(page_number)

def get_products():
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item' ))
    )
    html = browser.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'price': item.find('.price.g_price.g_price-highlight').text(),
            'deal': item.find('.deal-cnt').text()[:-3],
            'title': item.find('.row.row-2.title').text(),
            'shop': item.find('.shop').text(),
            'location': item.find('.location').text()
        }
        print(product)
        price = product['price']
        deal = product['deal']
        title = product['title']
        shop = product['shop']
        location = product['location']
        sql = "insert into products(price,deal,title,shop,location) values('%s', '%s', '%s', '%s', '%s');" % (price, deal, title, shop, location)
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
            conn.commit()
            print('数据插入成功')
        except Exception as e:
            print('数据插入失败')


def main():
    cursor.execute("create table if not exists products(price text, deal text, title text, shop text, location text)")
    total = search()
    total = int(re.compile('(\d+)').search(total).group(1))
    for i in range(2, total + 1):
        next_page(i)
    browser.close()
    conn.close()

if __name__ == '__main__':
    main()