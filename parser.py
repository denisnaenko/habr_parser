import json
import time

import requests
import urllib3
from bs4 import BeautifulSoup
from tqdm import tqdm

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OUTPUT_FILE = 'data.json'

def load_existing_data():
    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_data(data):
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_comments_html(article_url, article_author):
    comments_url = article_url.rstrip('/') + '/comments/'
    try:
        response = requests.get(comments_url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        comment_blocks = soup.find_all('div', class_='tm-comment__body-content')
        author_tags = soup.find_all('a', class_='tm-user-info__username')

        comments = []
        author_comments = []

        for block, author_tag in zip(comment_blocks, author_tags):
            comment_text = block.get_text(strip=True)
            author_name = author_tag.text.strip()
            comment_data = {'author': author_name, 'text': comment_text}
            comments.append(comment_data)
            if author_name == article_author:
                author_comments.append(comment_data)

        return comments, author_comments
    except Exception as e:
        print(f'⚠️ Ошибка при получении комментариев для {comments_url}: {e}')
        return [], []

def parse_article(url, existing_urls):
    if url in existing_urls:
        print(f'⏭ Пропускаю уже сохранённую статью: {url}')
        return None
    
    print(f'📄 Обрабатываю статью: {url}')
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f'❌ Ошибка при запросе {url}: {e}')
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    data = {}

    try:
        data['url'] = url
        data['title'] = soup.find('h1', class_='tm-title').text.strip()
        data['author'] = soup.find('span', class_='tm-user-info__user').text.strip().split(' ')[0]
        data['date'] = soup.find('time')['datetime']
        
        reading_time_tag = soup.find('span', class_='tm-article-reading-time__label')
        data['reading_time'] = reading_time_tag.text.strip() if reading_time_tag else None

        views_tag = soup.find_all('span', class_='tm-icon-counter__value')
        data['views'] = views_tag[-1].text.strip() if views_tag else None

        text_block = soup.find('div', id='post-content-body')
        data['text_content'] = text_block.get_text(separator='\n').strip() if text_block else ''

        images = text_block.find_all('img') if text_block else []
        data['image_content'] = [img['src'] for img in images if 'src' in img.attrs]

        tags = soup.find_all('a', class_='tm-tags-list__link')
        data['tags'] = [tag.text.strip() for tag in tags]

        comments, author_comments = get_comments_html(url, data['author'])
        data['comments'] = comments
        data['comments_from_author'] = author_comments

    except Exception as e:
        print(f'⚠️ Ошибка при парсинге содержимого {url}: {e}')
        return None

    return data

if __name__ == '__main__':
    with open('links.txt', 'r', encoding='utf-8') as f:
        article_urls = [line.strip() for line in f if line.strip()]

    existing_data = load_existing_data()
    existing_urls = {article['url'] for article in existing_data}
    
    results = existing_data
    save_every = 10
    
    for i, url in enumerate(tqdm(article_urls, desc="Обработка статей"), 1):
        result = parse_article(url, existing_urls)
        if result:
            results.append(result)
            existing_urls.add(url)
        
        if i % save_every == 0:
            save_data(results)
            print(f'💾 Промежуточное сохранение: {i} статей')

        time.sleep(1)

    save_data(results)
    print(f'✅ Всего сохранено {len(results)} статей в {OUTPUT_FILE}')