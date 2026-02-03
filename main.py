import os
import asyncio
from playwright.async_api import async_playwright
import requests
import re
from datetime import datetime, timedelta

# --- 설정 ---
TARGET_PRICE = 60000
DEPARTURE = "대구"
ARRIVAL = "제주"
# 내일 날짜
target_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

async def check_flights():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # 한국인이 사용하는 브라우저처럼 보이도록 더 상세하게 설정
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="ko-KR",
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()

        search_url = f"https://www.google.com/search?q={DEPARTURE}+{ARRIVAL}+항공권+{target_date}"
        print(f"구글 검색 접속 중: {search_url}")
        
        # 접속 시도
        await page.goto(search_url, wait_until="domcontentloaded")
        
        # 구글 항공권 모듈이 로딩될 시간을 충분히 줌 (10초)
        await page.wait_for_timeout(10000)

        # 페이지 전체에서 '원'이 포함된 텍스트 요소를 다 가져옴
        elements = await page.query_selector_all("span, div, b")
        
        fare_list = []
        for el in elements:
            text = await el.inner_text()
            
            # 1. '원'이 포함되어 있고 2. 숫자가 포함되어 있는지 확인
            if '원' in text and any(char.isdigit() for char in text):
                # 숫자만 추출 (예: '51,500원' -> '51500')
                clean_num = re.sub(r'[^0-9]', '', text)
                if clean_num:
                    price = int(clean_num)
                    # 항공권 가격 범위 필터링 (너무 작은 수나 너무 큰 수는 제외)
                    if 15000 < price < 300000:
                        fare_list.append(price)

        if not fare_list:
            print("데이터 추출 실패. 페이지 구조가 예상과 다릅니다.")
            # 디버깅을 위해 현재 페이지 텍스트 일부 출력
            content = await page.content()
            print("페이지 내 '원' 문자 존재 여부:", '원' in content)
        else:
            # 중복 제거 및 정렬
            fare_list = sorted(list(set(fare_list)))
            min_fare = fare_list[0]
            print(f"[{target_date}] 발견된 가격들: {fare_list[:5]}...") # 상위 5개 출력
            print(f"최종 최저가: {min_fare}원")
            
            if min_fare <= TARGET_PRICE:
                send_telegram(f"✈️ [구글검색 특가] {DEPARTURE}-{ARRIVAL}\n날짜: {target_date}\n최저가: {min_fare}원\n확인: {search_url}")
            else:
                print(f"알림 기준({TARGET_PRICE}원)보다 비쌉니다.")

        await browser.close()

def send_telegram(message):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            requests.get(url, params={"chat_id": chat_id, "text": message})
        except Exception as e:
            print(f"텔레그램 전송 실패: {e}")

if __name__ == "__main__":
    asyncio.run(check_flights())
