import os
import asyncio
from playwright.async_api import async_playwright
import requests
import re
from datetime import datetime, timedelta

# --- 설정 ---
TARGET_PRICE = 50000
DEPARTURE = "대구"
ARRIVAL = "제주"
target_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

async def check_flights():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # 중요: 언어와 타임존을 한국으로 강제 설정
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="ko-KR",
            timezone_id="Asia/Seoul",
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()

        # 구글 검색 URL 뒤에 &hl=ko&gl=kr 을 붙여 한국어/한국지역 결과를 강제합니다.
        search_url = f"https://www.google.com/search?q={DEPARTURE}+{ARRIVAL}+항공권+{target_date}&hl=ko&gl=kr"
        print(f"구글 검색(한국 설정) 접속 중: {search_url}")
        
        await page.goto(search_url, wait_until="domcontentloaded")
        
        # 1. 만약 '동의' 페이지나 '서비스 약관' 페이지가 뜨면 넘어가기 위한 대기
        await page.wait_for_timeout(5000)
        
        # 2. 항공권 모듈이 나타날 때까지 대기
        await page.wait_for_timeout(5000)

        # 페이지 제목 출력 (디버깅용)
        title = await page.title()
        print(f"현재 페이지 제목: {title}")

        # 3. 가격 추출 (원, KRW, ₩ 기호 모두 탐색)
        # 구글 항공권 모듈의 가격은 보통 특정 패턴 안에 있습니다.
        content = await page.content()
        
        # 가격 패턴 정규식: (숫자 1~3자리 + 쉼표 + 숫자 3자리) 뒤에 '원' 또는 'KRW' 또는 '₩'
        # 예: 51,500 / ₩51,500 / 51,500 KRW
        price_patterns = re.findall(r'([0-9]{1,3},[0-9]{3}|[0-9]{2,3}00)', content)
        
        fare_list = []
        for p_str in price_patterns:
            price = int(p_str.replace(',', ''))
            # 항공권 가격대인 것만 필터링 (2만 원 ~ 20만 원)
            if 20000 <= price <= 200000:
                fare_list.append(price)

        if not fare_list:
            print("데이터 추출 실패. 페이지 텍스트 분석 중...")
            # '원'이 없는 경우를 대비해 영어로 된 가격 단위가 있는지 확인
            if "KRW" in content: print("페이지에 'KRW' 단어가 존재합니다.")
            if "₩" in content: print("페이지에 '₩' 기호가 존재합니다.")
        else:
            fare_list = sorted(list(set(fare_list)))
            min_fare = fare_list[0]
            print(f"[{target_date}] 발견된 가격 리스트: {fare_list[:5]}")
            print(f"최종 최저가: {min_fare}원")
            
            if min_fare <= TARGET_PRICE:
                send_telegram(f"✈️ [항공권 특가 확인]\n날짜: {target_date}\n최저가: {min_fare}원\n검색결과: {search_url}")
            else:
                print(f"기준가({TARGET_PRICE}원)보다 비쌉니다.")

        await browser.close()

def send_telegram(message):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.get(url, params={"chat_id": chat_id, "text": message})

if __name__ == "__main__":
    asyncio.run(check_flights())
