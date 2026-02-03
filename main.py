import requests
import json
import os
from datetime import datetime, timedelta

# --- 설정 ---
TARGET_PRICE = 50000  # 알림 기준 가격
DEPARTURE_AIRPORT = "TAE" # 대구
ARRIVAL_AIRPORT = "CJU"   # 제주
# 오늘로부터 7일 후 날짜 (YYYYMMDD)
target_date = (datetime.now() + timedelta(days=7)).strftime('%Y%m%d')

def check_flights():
    # 네이버 항공권 모바일 API 엔드포인트
    url = f"https://m-flight.naver.com/api/flights/itinerary/list?adult=1&isDirect=true&stayLength=&fareType=Y&itinerary=[%7B%22departureAirportId%22:%22{DEPARTURE_AIRPORT}%22,%22arrivalAirportId%22:%22{ARRIVAL_AIRPORT}%22,%22departureDate%22:%22{target_date}%22%7D]&galileoFlag=true&travelAgencyList="

    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/04.1",
        "Referer": "https://m-flight.naver.com/"
    }

    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        # 항공권 목록 추출 (가장 저렴한 가격 찾기)
        flights = data.get('result', {}).get('flights', [])
        if not flights:
            print("항공권 정보를 찾을 수 없습니다.")
            return

        # 최저가 찾기
        min_fare = min([f['fare']['adt'] for f in flights])
        
        print(f"검색 날짜: {target_date}, 현재 최저가: {min_fare}원")

        if min_fare <= TARGET_PRICE:
            send_telegram(f"✈️ 대구-제주 특가 알림!\n날짜: {target_date}\n최저가: {min_fare}원\n얼른 확인하세요!")

    except Exception as e:
        print(f"에러 발생: {e}")

def send_telegram(message):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    params = {"chat_id": chat_id, "text": message}
    requests.get(url, params=params)

if __name__ == "__main__":
    check_flights()
