import os
import asyncio
from playwright.async_api import async_playwright
import requests
from datetime import datetime, timedelta

TARGET_PRICE = 50000
# 내일 날짜 (YYYY-MM-DD 형식, 구글은 이 형식을 선호합니다)
target_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

async def check_flights():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # 한국어 설정을 추가하여 한국어 결과를 유도합니다.
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            locale="ko-KR"
        )
        page = await context.new_page()

        # 구글에서 직접 검색 (네이버 차단을 피하기 위함)
        search_url = f"https://www.google.com/search?q=대구+제주+항공권+{target_date}"
        print(f"구글 검색 접속 중: {search_url}")
        
        await page.goto(search_url, wait_until="networkidle")
        await page.wait_for_timeout(5000) # 결과 로딩 대기

        # 구글 항공권 모듈에서 가격 텍스트 추출 (가격을 나타내는 일반적인 선택자 시도)
        # 구글은 클래스명이 유동적이므로 '원'이라는 글자를 포함한 요소를 찾습니다.
        price_elements = await page.query_selector_all("span:has-text('원')")
        
        fare_list = []
        for el in price_elements:
            text = await el.inner_text()
            try:
                # '35,000원' -> 35000 변환
                clean_text = ''.join(filter(str.isdigit, text))
                if clean_text:
                    fare_list.append(int(clean_text))
            except:
                continue

        if not fare_list:
            print("항공권 가격을 찾지 못했습니다. 다른 우회 방법을 고려해야 합니다.")
        else:
            min_fare = min([f for f in fare_list if f > 10000]) # 너무 낮은 가격(에러) 제외
            print(f"[{target_date}] 최저가 발견: {min_fare}원")
            
            if min_fare <= TARGET_PRICE:
                send_telegram(f"✈️ [특가 알림] 대구-제주\n날짜: {target_date}\n최저가: {min_fare}원\n검색결과: {search_url}")

        await browser.close()

def send_telegram(message):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.get(url, params={"chat_id": chat_id, "text": message})

if __name__ == "__main__":
    asyncio.run(check_flights())
