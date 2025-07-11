import requests
from bs4 import BeautifulSoup
from datetime import datetime
import xml.etree.ElementTree as ET
import sys

# 1. 爬取网页内容
def fetch_website_content(url):
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"无法访问网站: {url}")

# 2. 解析网页内容，获取资源列表
def parse_website(html):
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', class_='torrent-list')
    if not table:
        print("⚠️ 未找到资源表格")
        return []

    rows = table.find('tbody').find_all('tr')
    articles = []

    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 6:
            continue

        title_tag = cols[1].find('a')
        title = title_tag.get_text(strip=True) if title_tag else "未知标题"
        link = title_tag['href'] if title_tag else '#'

        # 构造完整链接（假设为 u3c3.com 域名下）
        full_link = f"https://u3c3.com{link}"

        pub_date_str = cols[4].get_text(strip=True)
        try:
            pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pub_date = datetime.now()

        articles.append({
            'title': title,
            'link': full_link,
            'description': f"类别: {cols[0].get_text(strip=True)}, 大小: {cols[3].get_text(strip=True)}",
            'pub_date': pub_date.strftime('%a, %d %b %Y %H:%M:%S +0000')
        })

    return articles

# 3. 生成 RSS Feed (XML 格式)
def generate_rss_feed(articles, site_title, feed_file):
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    ET.SubElement(channel, 'title').text = site_title
    ET.SubElement(channel, 'link').text = "https://u3c3.com/"
    ET.SubElement(channel, 'description').text = f"RSS Feed for {site_title}"

    for article in articles:
        item = ET.SubElement(channel, 'item')
        ET.SubElement(item, 'title').text = article['title']
        ET.SubElement(item, 'link').text = article['link']
        ET.SubElement(item, 'description').text = article['description']
        ET.SubElement(item, 'pubDate').text = article['pub_date']

    tree = ET.ElementTree(rss)
    tree.write(feed_file, encoding='utf-8', xml_declaration=True)

# 4. 生成 OPML 文件
def generate_opml_from_rss(rss_feed_url, opml_file):
    opml = ET.Element('opml', version='2.0')
    head = ET.SubElement(opml, 'head')
    ET.SubElement(head, 'title').text = "RSS Feeds"
    ET.SubElement(head, 'dateCreated').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
    ET.SubElement(head, 'dateModified').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')

    body = ET.SubElement(opml, 'body')
    outline = ET.SubElement(body, 'outline', {
        'type': 'rss',
        'text': rss_feed_url,
        'title': 'U3C3 最新资源',
        'xmlUrl': rss_feed_url
    })

    tree = ET.ElementTree(opml)
    tree.write(opml_file, encoding='utf-8', xml_declaration=True)

# 主函数：执行整个流程
def main(keyword=None):
    if keyword:
        url = f"https://u3c3.com/?search2=eelj1a3lfe1a1&search={keyword}"
    else:
        url = "https://u3c3.com/"

    print(f"🔍 抓取页面: {url}")
    html = fetch_website_content(url)
    articles = parse_website(html)

    if not articles:
        print("❌ 未解析到任何资源")
        return

    # 动态文件名
    feed_file = f"u3c3_feed_{keyword}.xml" if keyword else "u3c3_feed.xml"
    generate_rss_feed(articles, f"U3C3 - 搜索 [{keyword}]" if keyword else "U3C3 最新资源", feed_file)
    print(f"✅ {'搜索' if keyword else '首页'} RSS 已生成：{feed_file}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        keyword = sys.argv[1]
        main(keyword)
    else:
        main()
