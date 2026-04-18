import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone
import re

# --- [설정 부분] ---
MY_PASSWORD = "my1234!" 
API_KEY = "AIzaSyAzSS1UBeug7ljeDbsiihpzij0uij__HS0"
# 본인의 구글 시트 주소를 아래 따옴표 안에 넣으세요
MY_SHEET_URL = "https://docs.google.com/spreadsheets/d/194LW8FumvdaREqFZEwYZyeOTcy2U5sm6oTLKMY9yq2A/export?format=csv"

youtube = build('youtube', 'v3', developerKey=API_KEY)

# --- 채널 ID 추출 및 영상 수집 로직 ---
def get_channel_id(url):
    handle_match = re.search(r'@([\w\.-]+)', url)
    if handle_match:
        res = youtube.channels().list(part="id", forHandle=handle_match.group(1)).execute()
        return res['items'][0]['id'] if 'items' in res else None
    id_match = re.search(r'channel/(UC[\w-]+)', url)
    if id_match: return id_match.group(1)
    return None

def get_trending_videos(channel_urls):
    all_videos = []
    # --- 76시간(3일+4시간)으로 설정 ---
    time_threshold = datetime.now(timezone.utc) - timedelta(hours=76)
    
    for url in channel_urls:
        c_id = get_channel_id(str(url).strip())
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

# --- 웹 페이지 UI ---
st.set_page_config(page_title="76H YouTube Monitor", layout="wide")
st.title("🔐 자동 업데이트 분석기 (최근 76시간)") # 제목 수정

pwd_input = st.text_input("비밀번호 입력", type="password")

if pwd_input == MY_PASSWORD:
    st.success("인증 성공!")
    
    try:
        df = pd.read_csv(MY_SHEET_URL, header=None)
        channels = df[0].tolist()
        st.info(f"현재 구글 시트에서 {len(channels)}개의 채널을 불러왔습니다.")
    except:
        st.error("구글 시트를 불러오지 못했습니다. 주소와 공유 설정을 확인하세요.")
        channels = []

    if st.button("실시간 분석 시작"):
        if channels:
            with st.spinner('지난 76시간 동안의 영상을 찾는 중...'): # 문구 수정
                data = get_trending_videos(channels)
                if data: 
                    st.write(f"### 총 {len(data)}개의 영상을 발견했습니다.")
                    st.table(data)
                else: 
                    st.warning("최근 76시간 내에 업로드된 영상이 없습니다.") # 문구 수정
        else:
            st.error("분석할 채널 주소가 없습니다.")
