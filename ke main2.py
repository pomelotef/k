import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append("d:\python\ptt\.venv\lib\site-packages")
import os
from bs4 import BeautifulSoup
from urllib.request import urlopen, Request, urlretrieve
from urllib.parse import urlparse, parse_qs
import requests
import re
import pandas as pd
import urllib.error
import time


#算次數
count = 0

#檔案命名
def clean_filename(filename):
    return re.sub(r'[^\w.]+', '_', filename)

# 创建一个空的DataFrame，儲存連結用
df = pd.DataFrame(columns=["Attachment_Name", "Attachment_Link"])

#篩選網址用
def check_word(hide_url):
    global df
    keywords_w = ["drive.google", "dropbox", "mega"]
    keywords_b = ["www.pixiv", "discord.gg", "webcatalog","booth","melonbooks","www.amazon", "hoyolab.com", "www.patreon", "fanbox.cc", "patreon.com", "twitter.com", "gumroad.com", "dlsite.com", "fantia.jp"]
    for keyw in keywords_w:
        if re.search(keyw, hide_url):
            print("儲存：", hide_url)
            df = pd.concat([df, pd.DataFrame({"Attachment_Name": [None], "Attachment_Link": [hide_url]})], ignore_index=True)
            return
    for keyword in keywords_b:
        if re.search(keyword, hide_url):
            print("跳過：", hide_url)
            return  # 找到匹配时直接跳出函数
    else:
        print("儲存", hide_url)
        df = pd.concat([df, pd.DataFrame({"Attachment_Name": [None], "Attachment_Link": [hide_url]})], ignore_index=True)

#正则表达式，處理連結用
link_pattern = re.compile(r'https://\S+')

#輸入網址
full_url = input("請輸入欲抓取的最後一頁網址：")


#輸入範圍，沒輸入默認全抓

user_input = input("請輸入抓到第幾頁 (沒有要求直接按enter):")
user_creat = input("是否要單獨為post創立資料夾 (要：y/沒有要求直接按enter):")

if user_input:
    final = int(user_input)
else:
    final = 1
    


final_o = (final-1)*50

# 使用 urlparse 来解析网址 e.g.https://kemono.su/patreon/user/2443797?q=BlueArchive
parsed_url = urlparse(full_url)

#ParseResult(scheme='https', netloc='kemono.su', path='/patreon/user/2443797', params='',
#query='o=0&q=BlueArchive', fragment='')
# 从解析后的网址获取主要部分 https://kemono.su/patreon/user/2443797
all_url = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path
print("抓取user:"+all_url)

# 从查询参数中获取 o 和 q 参数
query_params = parse_qs(parsed_url.query)

page = int(query_params.get('o', [0])[0]) + 1
quest = query_params.get('q', ['0'])[0]

path = parsed_url.path
parts = path.split('/')
user_id = parts[-1]
user_type = parts[-3]
# 檢查輸入條件是否正確
print("頁數:"+str(page-1)+"；條件:"+quest)
if final > page:
    print("頁數範圍輸入錯誤")
    sys.exit(1)

    

# 创建以user id命名的文件夹
user_dirname = os.path.join(os.getcwd(), str(user_id))
if not os.path.exists(user_dirname):
    os.mkdir(user_dirname)


url_path = os.path.join(user_dirname, "url.txt")
with open(url_path, "w", encoding="utf-8") as file:
    # 将用户输入写入文件
    file.write(full_url)
print("内容已保存到output.txt文件中。")

#避免錯誤    
errornum = 0    
while True:
    try:
        for i in range(final_o, page, 50):
            link = f"{all_url}?o={i}&q={quest}"  # 注意这里使用 & 符号来添加查询参数  
            print(link)
            response = requests.get(link)
            soup = BeautifulSoup(response.text, features="html.parser")
            
            #找單個post網址 data-id   
            article_tag = soup.find_all('article')
            for post in article_tag:
                count = count + 1
                data_id = post.get('data-id')
                print("data-id:", data_id)
            
                #先檢查有沒有爬過
                post_dirname = os.path.join(user_dirname, str(data_id))
                if user_creat:
                    if os.path.exists(post_dirname):
                        print("資料夾已存在")
                    else:
                        os.mkdir(post_dirname)
            
                    
                #開爬單個post內的圖/網址/影片
                url = str(all_url)+"/post/"+str(data_id)
            
                response = requests.get(url)
                html = BeautifulSoup(response.text, features="html.parser")
                
                    # 将链接和文字添加到DataFrame中   
                #處理附加連結
                while True:
                    try:
                        print("處理附加連結")
                        post__attachments = html.find("ul", class_="post__attachments")
                        post__attachment_link = post__attachments.find_all("a", class_="post__attachment-link")
                        
                        # 将链接和文字添加到DataFrame中   
                        for p_link in post__attachment_link:
                            p_href = p_link.get("href")
                            p_text = p_link.text.strip()  # 使用 .text 属性获取标签内的文本并去除前后空白
                            print("儲存:",p_text ,p_href)
                            df = pd.concat([df, pd.DataFrame({"Attachment_Name": [p_text], "Attachment_Link": [p_href]})], ignore_index=True)
                        break
                    
                    except AttributeError:    
                        print("沒有附加連結")    
                        break  
                
                #處理內文連結      
                while True:
                    try:
                        print("處理內文連結") 
                        post__content = html.find("div", class_="post__content")
                        post__content_link = post__content.find_all("a", href = True)             
                        
                        for c_link in post__content_link:
                            c_href = c_link.get("href")
                            check_word(c_href)
                        break   
                            
                    except AttributeError:    
                        print("沒有內文連結")    
                        break      
                
                #處理文字連結
                while True:
                    try:
                        print("處理文字連結")
                        post__content = html.find("div", class_="post__content")
                        text_content = post__content.get_text(strip=True)
                        matches = link_pattern.findall(text_content)
                        # 提取的链接
                        for match in matches:
                            check_word(match)
                        break

                    except AttributeError:    
                        print("沒有文字連結")    
                        break        
               
        #找到單個圖片/gif/影片
                while True:
                    try:
                        post_files = html.find("div", class_="post__files")
                        a_tag = post_files.find_all("a", class_="fileThumb")
                        print("處理圖片")
                        #下載圖片
                        for index, a in enumerate(a_tag):
                            href = a.get("href")
                            if "gif" in href:
                                filename =str(data_id)+"_"+str(index)+".gif"
                            else:    
                                filename =str(data_id)+"_"+str(index)+".png"
                            #判斷是否要存到該post資料夾
                            if user_creat:                   
                                file_path = os.path.join(post_dirname, filename)
                            else:
                                file_path = os.path.join(user_dirname, filename)
                                
                            #檢測有沒有存過        
                            if os.path.exists(file_path):
                                print("檔案已存在")
                                
                            else:
                                start_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
                                print(start_time_str)
                                urlretrieve(href, file_path)
                                print(href)
                                
                        print(str(user_type)+"_"+str(user_id)+"_"+str(data_id),"下載完了")    
                        break          
                    except AttributeError:
                        print("沒有圖片")        
                        break   
        break 
                       
    except urllib.error.ContentTooShortError as e:
        errornum += 1
        print(f"ContentTooShortError: {e}")
        print("Retrying...")
        print(errornum)
        time.sleep(1)  # 可以選擇添加延遲，避免過於頻繁地重試
    
          
print("全部抓取完，共"+str(count)+"個post，輸出連結")   
     
df.to_csv(str(user_type)+"_"+str(user_id)+"_"+str(quest)+".csv", index=False)
input("爬完了")
            

        

