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

# 대기질 데이터 조회 함수
def get_air_quality_data(sido):
    url = ''
    params = {
        'serviceKey': '', 
        'returnType': 'json', 
        'numOfRows': '100', 
        'pageNo': '1', 
        'sidoName': sido, 
        'ver': '1.0'
    }
    response = requests.get(url, params=params)
    content = response.content.decode('utf-8')
    data = json.loads(content)
    return data

# 대기질 데이터 파싱 함수
def parse_air_quality_data(data):
    items = data['response']['body']['items']
    air_quality_info = []
    for item in items:
        info = {
            '측정소명': item.get('stationName'),
            '날짜': item.get('dataTime'),
            '미세먼지농도': item.get('pm10Value'),
            '초미세먼지농도': item.get('pm25Value'),
            'so2농도': item.get('so2Value'),
            'co농도': item.get('coValue'),
            'o3농도': item.get('o3Value'),
            'no2농도': item.get('no2Value'),
            '통합대기환경수치': item.get('khaiValue'),
            '통합대기환경지수': item.get('khaiGrade'),
            '미세먼지등급': item.get('pm10Grade'),
            '초미세먼지등급': item.get('pm25Grade')
        }
        air_quality_info.append(info)
    return air_quality_info

# 메인 스트림릿 앱
def main():
    st.title("대기질 정보 제공 챗봇")

    # 사용자 입력
    sido = st.text_input("도시 이름을 입력하세요:", "서울")
    query = st.text_input("궁금한 지역을 입력하세요:", "중랑구")
    
    if st.button("지역 선택"):
        data = get_air_quality_data(sido)
        air_quality_info = parse_air_quality_data(data)

        documents = [
            Document(page_content=", ".join([f"{key}: {str(info[key])}" for key in ['측정소명', '날짜', '미세먼지농도', '초미세먼지농도', '통합대기환경수치']])) 
            for info in air_quality_info
        ]

        text_splitter = RecursiveCharacterTextSplitter(separators=",")
        docs = text_splitter.split_documents(documents)

        embedding_function = SentenceTransformerEmbeddings(model_name="jhgan/ko-sroberta-multitask")

        db = FAISS.from_documents(docs, embedding_function)
        retriever = db.as_retriever(search_type="similarity", search_kwargs={'k':5, 'fetch_k': 100})
               
        if query:
            query_result = db.similarity_search(query)
            st.write("DB검색 결과",query_result[0].page_content)
            

            # 챗봇 설정
            llm = ChatOllama(model="gemma2:9b", temperature=0.3)

            template = """
            당신은 대기질을 안내하는 챗봇입니다. 
            사용자에게 가능한 많은 정보를 친절하게 제공하십시오.            
            다음의 기준으로, 공기가 좋음, 보통, 나쁨, 매우 나쁨을 판별해주세요. 
            
            PM10 (미세먼지 농도)
                좋음: 0 ~ 30 
                보통: 31 ~ 80
                나쁨: 81 ~ 150 
                매우 나쁨: 151 이상
            PM2.5 (초미세먼지 농도)
                좋음: 0 ~ 15 
                보통: 16 ~ 35 
                나쁨: 36 ~ 75 
                매우 나쁨: 76 이상
            
            Answer the question as based only on the following context:
            {context}

            Question: {question}
            """
            prompt = ChatPromptTemplate.from_template(template)

            chain = RunnableMap({
                "context": lambda x: retriever.get_relevant_documents(x['question']),
                "question": lambda x: x['question']
            }) | prompt | llm

            question = query
            if question:
                response = chain.invoke({'question': question})
                st.markdown(response.content)

if __name__ == "__main__":
    main()