import requests
import re
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin

#获取URl的text

def getHTMLText(url):
    try:
        re = requests.get(url, timeout =30)
        re.raise_for_status()
        re.encoding = re.apparent_encoding
        return re.text
    except:
        return""

# 使用正常的字符替换HTML中特殊的字符实体.

def replaceCharEntity(htmlstr):
    CHAR_ENTITIES = {'nbsp': ' ', '160': ' ',
                     'lt': '<', '60': '<',
                     'gt': '>', '62': '>',
                     'amp': '&', '38': '&',
                     'quot': '"', '34': '"', }

    re_charEntity = re.compile(r'&#?(?P<name>\w+);')
    sz = re_charEntity.search(htmlstr)
    while sz:
        entity = sz.group()  # entity全称，如&gt;
        key = sz.group('name')  # 去除&;后entity,如&gt;为gt
        try:
            htmlstr = re_charEntity.sub(CHAR_ENTITIES[key], htmlstr, 1)
            sz = re_charEntity.search(htmlstr)
        except KeyError:
            # 以空串代替
            htmlstr = re_charEntity.sub('', htmlstr, 1)
            sz = re_charEntity.search(htmlstr)
    return htmlstr

#除去网页内容中的各种标签以及干扰项

def HTMLClear(text):
    re_cdata = re.compile('//<!\[CDATA\[[^>]*//\]\]>',re.I) #匹配CDATA
    re_br = re.compile('<br\s*?/?>')#处理换行
    re_h = re.compile('</?\w+[^>]*>')#HTML标签
    re_comment = re.compile('<!--[^>]*-->')#HTML注释
    s = re_cdata.sub('',text)#去掉CDATA
    s = re_br.sub('',s)#将br转换为换行
    s = re_h.sub('',s) #去掉HTML 标签
    s = re_comment.sub('',s)#去掉HTML注释
    s = re.sub('\\t', '', s)
    s = replaceCharEntity(s)#替换实体
    return s

#根据行块密度分布算法获取网页正文内容

def ContentExtractor(text, clock_width , threshold):
    count_block = []
    indexDistribution = []
    mains = []  #记录正文行号
    start_bool = False
    end_bool = False
    #计算每个行块的文字数量
    lines = text.splitlines()
    for line in lines:
        indexDistribution.append(len(line))#计算每行字数
    for i in range(len(text.splitlines()) - clock_width):
        count_block.append(0)
        for j in range(clock_width):
            count_block[i] += indexDistribution[i + j]#累加行块中每行的字数
    len_cblock = len(count_block)

    #筛选正文
    for index in range(len_cblock - 1):
        if count_block[index] > threshold and not start_bool :
            if (count_block[index + 1] != 0 or count_block[index + 2] != 0 or count_block[index + 3] != 0):
                start_bool = True
                begining = index
            continue
        if start_bool:
            if (count_block[index] == 0 or count_block[index + 1] == 0 ):
                end = index
                end_bool = True
        tmp = []
        if end_bool:
            for li in range(begining, end + 1):
                if(len(lines[li]) < 5 ):
                    continue
                for i in range(clock_width):
                    if li + i not in mains:
                        mains.append(li + i)
                start_bool = end_bool = False
    for i in mains:
        tmp.append(lines[i] + '\n')
    result = "".join(list(tmp))
    return result

#获取单HTML页面链接队列

def getHTMLQueue(tList, start_url):
    tList.append(start_url)
    html  = getHTMLText(start_url)
    soup = BeautifulSoup(html, 'html.parser')

    urls = []
    alist = soup.find_all("a", href = re.compile('.*'))
    for i in range(len(alist)):
        try:
            temp = alist[i]['href']
            urls.append(urljoin(start_url, temp))
            if urls[i] not in tList:
                tList.append(urls[i])
        except:
            continue

#获取网页正文内容

def getHTMLInfo(html, clock_width, threshold):
    try:
        text = HTMLClear(html)
        maintext = ContentExtractor(text, clock_width, threshold)
        return maintext
    except:
        return""

#保存网页

def SaveHtml(fpath, url, clock_width, threshold):
    if not os.path.exists(fpath):
        os.mkdir(fpath)

    html = getHTMLText(url)
    soup = BeautifulSoup(html, 'html.parser')

    # 除去script和style，re库除不干净
    scripts = soup.find_all("script")
    styles = soup.find_all("style")
    for script in scripts:
        script.decompose()
    for style in styles:
        style.decompose()
    text = soup.get_text()
    try:
        title = soup.find_all('title')[0].string
        maintext = getHTMLInfo(text, clock_width, threshold)
        English_only = ''.join(x for x in maintext if ord(x) < 256)
        path = fpath + '/' + title + '.txt'
        if  not os.path.exists(path):
            with open(path, 'w') as f:
                f.write(url)
                f.write(title + '\n')
                f.write(English_only)
                f.close()
    except:
        print("Wrong!")

def main():
    start_url = "http://news.qq.com/a/20170504/030186.htm"
    fpath = "F:/NetSpider"
    tList = []
    depth = 1
    clockwidth = 3
    threshold = 80

    count = 0
    tList.append(start_url)
    for i in range(depth):
        for j in range(count, len(tList)):
            getHTMLQueue(tList, tList[count])

    maxcount = len(tList)
    count = 0
    for i in range(len(tList)):
        try:
            SaveHtml(fpath, tList[i], clockwidth, threshold)
            count = count + 1
            print("\r进度:{:.2f}%".format(count * 100 / maxcount),end = "")
        except:
            continue

main()