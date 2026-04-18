import streamlit as st
from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone
import re

# --- [수정할 부분 1] 내 비밀번호 설정 ---
MY_PASSWORD = "my1234!"  # 원하는 비밀번호로 바꾸세요!

# --- [수정할 부분 2] 내 유튜브 API 열쇠 ---
API_KEY = "YOUR_YOUTUBE_API_KEY" # 지난번에 받은 API 키를 여기에 넣으세요!

youtube = build('youtube', 'v3', developerKey=API_KEY)

# --- 유틸리티 함수 및 로직 (동일) ---
def get_channel_id(url):
    handle_match = re.search(r'@([\w\.-]+)', url)
    if handle_match:
        res = youtube.channels().list(part="id", forHandle=handle_match.group(1)).execute()
        return res['items'][0]['id'] if 'items' in res else None
    id_match = re.search(r'channel/(UC[\w-]+)', url)
    if id_match:
        return id_match.group(1)
    return None

def get_trending_videos(channel_urls):
    all_videos = []
    time_threshold = datetime.now(timezone.utc) - timedelta(days=1)
    for url in channel_urls:
        c_id = get_channel_id(url.strip())
        if not c_id: continue
        res = youtube.activities().list(part="snippet,contentDetails", channelId=c_id, maxResults=5).execute()
        video_ids = []
        for item in res.get('items', []):
            if item['snippet']['type'] == 'upload':
                pub_at = datetime.strptime(item['snippet']['publishedAt'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                if pub_at > time_threshold:
                    video_ids.append(item['contentDetails']['upload']['videoId'])
        if video_ids:
            v_res = youtube.videos().list(part="snippet,statistics", id=",".join(video_ids)).execute()
            for v in v_res.get('items', []):
                all_videos.append({
                    "채널명": v['snippet']['channelTitle'],
                    "영상 제목": v['snippet']['title'],
                    "조회수": int(v['statistics'].get('viewCount', 0)),
                    "링크": f"https://youtu.be/{v['id']}"
                })
    return sorted(all_videos, key=lambda x: x['조회수'], reverse=True)

# --- 웹 페이지 UI 구성 ---
st.set_page_config(page_title="24H YouTube Trending", layout="wide")

# --- 비밀번호 체크 로직 ---
st.title("🔐 비밀번호가 필요한 서비스입니다")
pwd_input = st.text_input("비밀번호를 입력하세요", type="password")

if pwd_input == MY_PASSWORD:
    st.success("인증 성공!")
    st.divider() # 줄 긋기
    
    # 여기서부터 원래 프로그램 내용
    st.subheader("📊 채널별 최근 24시간 인기 영상 분석")
    urls_input = st.text_area("유튜브 채널 링크를 입력하세요 (한 줄에 하나씩)", height=150)
    analyze_button = st.button("실시간 분석 시작")

    if analyze_button and urls_input:
        urls = urls_input.split('\n')
        with st.spinner('데이터를 분석 중입니다...'):
            data = get_trending_videos(urls)
            if data:
                st.table(data)
            else:
                st.warning("최근 24시간 내에 업로드된 영상이 없습니다.")
else:
    if pwd_input != "":
        st.error("비밀번호가 틀렸습니다.")
    st.info("비밀번호를 입력해야 분석 기능을 사용할 수 있습니다.")
