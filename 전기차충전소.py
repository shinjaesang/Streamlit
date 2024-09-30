import os
import json
import datetime
import streamlit as st
import ollama
import requests
import xml.etree.ElementTree as ET
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# 전기차 충전소 API URL
url = ''

# 서울특별시 구 이름과 코드 매핑
gu_code_mapping = {
    "종로구": "11110",
    "중구": "11140",
    "용산구": "11170",
    "성동구": "11200",
    "광진구": "11215",
    "동대문구": "11230",
    "중랑구": "11260",
    "성북구": "11290",
    "강북구": "11305",
    "도봉구": "11320",
    "노원구": "11350",
    "은평구": "11380",
    "서대문구": "11410",
    "마포구": "11440",
    "양천구": "11470",
    "강서구": "11500",
    "구로구": "11530",
    "금천구": "11545",
    "영등포구": "11560",
    "동작구": "11590",
    "관악구": "11620",
    "서초구": "11650",
    "강남구": "11680",
    "송파구": "11710",
    "강동구": "11740"
}

# 전기차 충전소 정보 조회 함수
def get_charger_data(gu_code):
    params = {
        'serviceKey': '',  # 자신의 서비스 키로 교체
        'pageNo': '1',
        'numOfRows': '100',
        'dataType': 'xml',
        'zscode': gu_code
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.text
        return data
    else:
        st.error("API 호출 실패: " + str(response.status_code))
        return None

# 전기차 충전소 데이터 파싱 함수
def parse_charger_data(data):
    root = ET.fromstring(data)
    charger_info = []

    for item in root.findall('.//item'):
        info = {
            '충전소명': item.find('statNm').text,
            '주소': item.find('addr').text,
            '충전기타입': item.find('chgerType').text,
            '이용가능시간': item.find('useTime').text,
            '운영기관': item.find('busiNm').text,
            '위도': float(item.find('lat').text),
            '경도': float(item.find('lng').text)
        }
        charger_info.append(info)
    
    return charger_info

# Ollama 챗봇을 통해 질문 및 응답 제공 함수
def st_ollama(model_name, user_question, params):
    messages = [{"content": f"{user_question}", "role": "user"}]

    if params.get("system"):
        messages.insert(0, {"role": "system", "content": params["system"]})

    response = ollama.chat(
        model_name,
        messages,
        options={k: v for k, v in params.items() if k != "system"}
    )

    return response['message']['content']

# 메인 스트림릿 앱
def main():
    st.title("서울 전기차 충전소 정보 제공 챗봇")
    
    query = st.text_input("전기차 충전소 관련 질문을 입력하세요. ")

    if st.button("질문하기"):
        if query:
            llm_name = 'gemma2:9b'
            params = {
                "system": "사용자가 궁금해하는 위치의 전기차 충전소 정보를 친절하게 제공하세요.",
                "num_predict": 1024,
                "temperature": 0.3,
                "top_k": 40,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
                "presence_penalty": 0.0,
                "frequency_penalty": 0.0,
                "seed": 1
            }
            
            # Ollama를 통해 질문에 대한 응답 생성
            response_message = st_ollama(llm_name, query, params)

            # 구 이름 추출
            for gu_name in gu_code_mapping.keys():
                if gu_name in response_message:
                    gu_code = gu_code_mapping[gu_name]
                    break
            else:
                st.write("구 이름을 찾을 수 없습니다.")
                return

            # 해당 구의 충전소 데이터 가져오기
            charger_data = get_charger_data(gu_code)
            if charger_data:
                charger_info = parse_charger_data(charger_data)

                if charger_info:
                    for info in charger_info:
                        st.markdown(f"""
                        - **충전소명**: {info['충전소명']}  
                        - **주소**: {info['주소']}  
                        - **충전기타입**: {info['충전기타입']}  
                        - **이용가능시간**: {info['이용가능시간']}  
                        - **운영기관**: {info['운영기관']}  
                        - **위도**: {info['위도']}  
                        - **경도**: {info['경도']}  
                        """)
                else:
                    st.write("해당 구에 충전소 정보가 없습니다.")
            else:
                st.write("충전소 정보를 가져오는 데 실패했습니다.")
        else:
            st.write("질문을 입력하세요.")

if __name__ == "__main__":
    main()
