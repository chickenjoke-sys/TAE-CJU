import os
import asyncio
from playwright.async_api import async_playwright
import requests

# --- 설정 ---
TARGET_PRICE = 50000
DEPARTURE = "TAE"
ARRIVAL = "CJU"
# 오늘로부터 7일 후 날짜 계산
from datetime import datetime, timedelta
target_date = (datetime.now() + timedelta(days=1)).strftime('%Y%m%d')

async def check_flights():
    async with async_playwright() as p:
        # 브라우저 실행 (실제 사람처럼 보이기 위해 헤드리스 모드 사용)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # 네이버 항공권 검색 결과 페이지로 바로 이동
        url = f"https://m-flight.naver.com/flights/itinerary/{DEPARTURE}-{ARRIVAL}-{target_date}?adult=1&isDirect=true&fareType=Y"
        print(f"접속 중: {url}")
        
        await page.goto(url, wait_until="networkidle")
        
        # 항공권 정보가 로딩될 때까지 잠시 대기 (최대 10초)
        try:
            await page.wait_for_selector(".domestic_Flight__3uV_j", timeout=15000)
        except:
            print("항공권 정보를 찾는 데 실패했습니다. (로딩 지연 또는 결과 없음)")
            await browser.close()
            return

        # 모든 가격 요소 추출
        prices = await page.query_selector_all(".domestic_num__2roTW")
        
        fare_list = []
        for price_el in prices:
            text = await price_el.inner_text()
            # '12,500' 형태의 문자열을 숫자로 변환
            num = int(text.replace(",", ""))
            fare_list.append(num)

        if not fare_list:
            print("가격 데이터를 가져오지 못했습니다.")
        else:
            min_fare = min(fare_list)
            print(f"최저가 발견: {min_fare}원")
            
            if min_fare <= TARGET_PRICE:
                send_telegram(f"✈️ [레이커스 항공] 대구-제주 특가!\n날짜: {target_date}\n최저가: {min_fare}원\n확인: {url}")
        
        await browser.close()

def send_telegram(message):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.get(url, params={"chat_id": chat_id, "text": message})

if __name__ == "__main__":
    asyncio.run(check_flights())
