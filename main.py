import requests
import os
from datetime import datetime, timedelta

# --- 설정 ---
TARGET_PRICE = 50000
DEPARTURE_AIRPORT = "TAE"
ARRIVAL_AIRPORT = "CJU"
# 검색 날짜: 내일로부터 7일 후 (날짜가 너무 멀면 표가 없을 수 있음)
target_date = (datetime.now() + timedelta(days=1)).strftime('%Y%m%d')

def check_flights():
    # URL을 직접 조립하지 않고 params로 넘겨서 인코딩 문제를 방지합니다.
    url = "https://m-flight.naver.com/api/flights/itinerary/list"
    
    params = {
        "adult": "1",
        "isDirect": "true",
        "fareType": "Y",
        "itinerary": f'[{{"departureAirportId":"{DEPARTURE_AIRPORT}","arrivalAirportId":"{ARRIVAL_AIRPORT}","departureDate":"{target_date}"}}]',
        "galileoFlag": "true"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/04.1",
        "Referer": "https://m-flight.naver.com/flights/itinerary/TAE-CJU-20240520?adult=1&isDirect=true&fareType=Y",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        
        # 상태 코드 확인 (200이 아니면 차단된 것)
        print(f"응답 상태 코드: {response.status_code}")
        
        if response.status_code != 200:
            print("네이버에서 요청을 차단했습니다. 헤더나 IP를 확인해야 합니다.")
            return

        data = response.json()
        
        # 항공권 목록 확인
        flights = data.get('result', {}).get('flights', [])
        
        if not flights:
            print(f"{target_date}에 해당하는 항공권 정보가 없습니다.")
            return

        # 가격 추출 및 최저가 계산
        prices = [f['fare']['adt'] for f in flights if 'fare' in f]
        if not prices:
            print("가격 정보가 포함된 항공권이 없습니다.")
            return
            
        min_fare = min(prices)
        print(f"검색 날짜: {target_date}, 현재 최저가: {min_fare}원")

        if min_fare <= TARGET_PRICE:
            send_telegram(f"✈️ 레이커스 항공 특가!\n날짜: {target_date}\n최저가: {min_fare}원\n확인: https://m-flight.naver.com/")
        else:
            print(f"알림 기준({TARGET_PRICE}원)보다 비쌉니다. (현재 {min_fare}원)")

    except Exception as e:
        print(f"에러 상세 내용: {e}")

def send_telegram(message):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("텔레그램 토큰 또는 ID가 설정되지 않았습니다.")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    params = {"chat_id": chat_id, "text": message}
    requests.get(url, params=params)

if __name__ == "__main__":
    check_flights()
