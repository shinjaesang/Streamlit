# import streamlit as st
# import json
# import requests
# from langchain_community.vectorstores import FAISS
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain.schema import Document
# from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
# from langchain_community.chat_models import ChatOllama
# from langchain.prompts import ChatPromptTemplate
# from langchain.schema.runnable import RunnableMap

# # 기상 데이터 조회 함수
# def get_weather_data(district):
#     url = '  # 기상 API 엔드포인트
#     params = {
#         'key': '',  # 기상 API 키
#         'q': district,  # 사용자가 입력한 구
#         'lang': 'ko'
#     }
#     response = requests.get(url, params=params)
#     return json.loads(response.content)

# # 메인 스트림릿 앱
# def main():
#     st.title("서울 구별 실시간 기상 정보 제공 챗봇")

#     # 사용자 입력
#     district = st.text_input("구 이름을 입력하세요:", "중랑구")
    
#     if st.button("구 검색"):
#         weather_data = get_weather_data(district)
        
#         # 기상 정보 추출
#         current_weather = weather_data['current']
#         weather_info = {
#             '위치': weather_data['location']['name'],
#             '온도(°C)': current_weather['temp_c'],
#             '습도(%)': current_weather['humidity'],
#             '풍속(km/h)': current_weather['wind_kph'],
#             '날씨': current_weather['condition']['text']
#         }

#         # 정보 표시
#         st.write("현재 기상 정보:")
#         for key, value in weather_info.items():
#             st.write(f"{key}: {value}")

#         # 챗봇 설정
#         llm = ChatOllama(model="gemma2:9b", temperature=0.3)

#         template = """
#         당신은 기상정보를 안내하는 챗봇입니다. 
#         사용자에게 가능한 많은 정보를 친절하게 제공하십시오.
        
#         Answer the question as based only on the following context:
#         {context}

#         Question: {question}
#         """
#         prompt = ChatPromptTemplate.from_template(template)

#         # 사용자 질문 처리
#         question = st.text_input("궁금한 점을 입력하세요:")
#         if question:
#             context = f"{weather_info}"
#             response = llm.invoke({"context": context, "question": question})
#             st.markdown(response.content)

# if __name__ == "__main__":
#     main()



import streamlit as st
import json
import requests
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnableMap

key = '

# 기상 데이터 조회 함수
def get_weather_data(sido, key):
    url = ''
    params = {
        'serviceKey': key,
        'pageNo': '1',
        'numOfRows': '1000',
        'dataType': 'json',
        'base_date': '20210628',  # 이 날짜는 현재 날짜로 변경할 수 있습니다
        'base_time': '0600',  # 이 시간도 현재 시간으로 변경할 수 있습니다
        'nx': '55',  # 서울의 X좌표
        'ny': '127'  # 서울의 Y좌표
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        st.error("Failed to retrieve data.")
        return None
    return json.loads(response.content)

    # 응답 상태 코드 확인
    if response.status_code != 200:
        st.error("기상 데이터 요청에 실패했습니다.")
        return None

    # 응답 내용 출력
    try:
        return json.loads(response.content)
    except json.JSONDecodeError:
        st.error("응답 데이터가 올바르지 않습니다.")
        return None

# 메인 스트림릿 앱
def main():
    st.title("서울 구별 실시간 기상 정보 제공 챗봇")

    # 사용자 입력
    district = st.text_input("구 이름을 입력하세요:", "중랑구")
    
    if st.button("구 검색"):
        weather_data = get_weather_data(district)
        
        if weather_data is not None:
            # 기상 정보 추출
            current_weather = weather_data['current']
            weather_info = {
                '위치': weather_data['location']['name'],
                '온도(°C)': current_weather['temp_c'],
                '습도(%)': current_weather['humidity'],
                '풍속(km/h)': current_weather['wind_kph'],
                '날씨': current_weather['condition']['text']
            }

            # 정보 표시
            st.write("현재 기상 정보:")
            for key, value in weather_info.items():
                st.write(f"{key}: {value}")

            # 챗봇 설정
            llm = ChatOllama(model="gemma2:9b", temperature=0.3)

            template = """
            당신은 기상정보를 안내하는 챗봇입니다. 
            사용자에게 가능한 많은 정보를 친절하게 제공하십시오.
            
            Answer the question as based only on the following context:
            {context}

            Question: {question}
            """
            prompt = ChatPromptTemplate.from_template(template)

            # 사용자 질문 처리
            question = st.text_input("궁금한 점을 입력하세요:")
            if question:
                context = f"{weather_info}"
                response = llm.invoke({"context": context, "question": question})
                st.markdown(response.content)

if __name__ == "__main__":
    main()
