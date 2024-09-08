import requests
from bs4 import BeautifulSoup
import sqlite3
import re
import time
memory = []
# SQLite 데이터베이스 연결 (또는 다른 DB로 교체 가능)
conn = sqlite3.connect('filter_words.db')
cursor = conn.cursor()
conn.commit()
def get_lowest_frequency_word():
    """빈도수가 가장 낮은 키워드를 가져오고, 그 키워드의 빈도수를 2만큼 증가시키는 함수"""
    conn = sqlite3.connect('filter_words.db')
    c = conn.cursor()
    
    # 빈도수(cnt)가 가장 낮은 키워드를 하나 가져오는 쿼리
    c.execute('''
        SELECT word, cnt
        FROM bad_words
        ORDER BY cnt ASC
        LIMIT 1
    ''')
    
    row = c.fetchone()  # 하나의 결과만 가져오기
    
    if row:
        word, cnt = row
        # 해당 키워드의 빈도수를 +2 만큼 증가
        c.execute('''
            UPDATE bad_words
            SET cnt = cnt + 2
            WHERE word = ?
        ''', (word,))
        conn.commit()  # 변경사항 저장
    
    return row
def search_youtube_videos(search_query, max_results=20):
    # 유튜브 검색어로 비디오 ID를 검색 (크롤링 방식)
    search_url = f"https://www.youtube.com/results?search_query={search_query}"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    soup = str(soup)
    pattern = r'\/watch\?v=([^"&]+)'  # /watch?v= 뒤에 오는 비디오 ID 추출
    matches = re.findall(pattern, soup)
    matches = list(set(matches))  # 중복 제거
    
    # 비디오 ID는 항상 11글자이므로, 11글자까지만 추출
    video_ids = [match[:11] for match in matches]
    
    # 최대 max_results만큼 반환
    return video_ids[:max_results]

def get_video_comments(video_id,key,lange):
# YouTube API로부터 댓글 데이터 가져오기
    memory.append(video_id)
    url = f'https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&key={key}'
    start = lange[0]
    end = lange[1]
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"Error fetching YouTube comments: {e}")

        return
    answer = ''

    # 댓글 데이터 처리 및 API 요청
    for i in range(start, min(end, len(data.get('items', [])))):
        comment = data['items'][i]['snippet']['topLevelComment']['snippet']['textDisplay']
        print(f"Comment: {comment}")
        data2 = {"document": comment}
        
        headers = {
            "Content-Type": "application/json",
            "x-auth-token": "918658b0-cc4b-4304-a8ca-8ac850c16ed7"
        }
        answer += comment + ' '
    return answer
# 함수 사용 예시
def add_keyword(repeat,search_query):
    video_ids = search_youtube_videos(search_query)
    if repeat == 0:
        return
    for video_id in video_ids:
        print(f"비디오 ID: {video_id}")
        
        comments = get_video_comments(video_id,"AIzaSyAVnteL9JlOKZwa0cUk52PgpuqVYi7rZZQ",(0,30))
        print("댓글에 포함된 단어:", comments)

        sample = requests.post("http://127.0.0.1:5000/chk", json={"text": comments})
        if sample.status_code != 500:
            print(sample.json())
            for res in sample.json():
                if res != '욕아님':
                    cursor.execute('''
                        INSERT INTO bad_words (word, cnt)
                        VALUES (?, 1)
                        ON CONFLICT(word) DO UPDATE SET cnt = cnt + 1
                    ''', (res,))
                    conn.commit()
                    print("욕설 단어 저장됨 또는 cnt 증가:", res)
    row = get_lowest_frequency_word()[0]

    print("새로운 키워드 : ",row)
    return add_keyword(repeat-1,row)
# 데이터베이스 연결 종료
add_keyword(20,'병@신')
conn.close()
