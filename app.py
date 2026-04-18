import streamlit as st
from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone
import re

# --- 1. API 설정 ---
API_KEY = "AIzaSyAzSS1UBeug7ljeDbsiihpzij0uij__HS0" # 본인의 API 키 입력
youtube = build('youtube', 'v3', developerKey=API_KEY)

# --- 2. 유틸리티 함수: URL에서 채널 ID 추출 ---
def get_channel_id(url):
    # 핸들(@name) 형식 처리
    handle_match = re.search(r'@([\w\.-]+)', url)
    if handle_match:
        res = youtube.channels().list(part="id", forHandle=handle_match.group(1)).execute()
        return res['items'][0]['id'] if 'items' in res else None
    
    # 채널 ID(channel/UC...) 형식 처리
    id_match = re.search(r'channel/(UC[\w-]+)', url)
    if id_match:
        return id_match.group(1)
    return None

# --- 3. 핵심 로직: 영상 수집 및 분석 ---
def get_trending_videos(channel_urls):
    all_videos = []
    time_threshold = datetime.now(timezone.utc) - timedelta(days=1)

    for url in channel_urls:
        c_id = get_channel_id(url.strip())
        if not c_id: continue

        # 최근 활동 가져오기 (1포인트)
        res = youtube.activities().list(part="snippet,contentDetails", channelId=c_id, maxResults=5).execute()

        video_ids = []
        for item in res.get('items', []):
            if item['snippet']['type'] == 'upload':
                pub_at = datetime.strptime(item['snippet']['publishedAt'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                if pub_at > time_threshold:
                    video_ids.append(item['contentDetails']['upload']['videoId'])

        if video_ids:
            # 영상 상세 정보(조회수) 가져오기 (1포인트)
            v_res = youtube.videos().list(part="snippet,statistics", id=",".join(video_ids)).execute()
            for v in v_res.get('items', []):
                all_videos.append({
                    "채널명": v['snippet']['channelTitle'],
                    "영상 제목": v['snippet']['title'],
                    "조회수": int(v['statistics'].get('viewCount', 0)),
                    "링크": f"https://youtu.be/{v['id']}"
                })

    return sorted(all_videos, key=lambda x: x['조회수'], reverse=True)

# --- 4. 웹 페이지 UI 구성 ---
st.set_page_config(page_title="24H YouTube Trending", layout="wide")
st.title("📊 채널별 최근 24시간 인기 영상 분석")

urls_input = st.text_area("유튜브 채널 링크를 입력하세요 (한 줄에 하나씩, 최대 20개)", height=150)
analyze_button = st.button("실시간 분석 시작")

if analyze_button and urls_input:
    urls = urls_input.split('\n')
    with st.spinner('데이터를 분석 중입니다...'):
        data = get_trending_videos(urls)
        
        if data:
            st.success(f"총 {len(data)}개의 영상을 찾았습니다.")
            # 표 형태로 출력
            st.table(data)
        else:
            st.warning("최근 24시간 내에 업로드된 영상이 없습니다.")
