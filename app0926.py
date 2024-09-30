import streamlit as st
import json
import requests
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnableMap

# Replace this with your actual API key
key = '  # Use an environment variable or secure method in production

def seoul_pm_query(sido, key):
    url = ''
    params = {
        'serviceKey': key,
        'returnType': 'json',
        'numOfRows': '100',
        'pageNo': '1',
        'sidoName': sido,
        'ver': '1.0'
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        st.error("Failed to retrieve data.")
        return None
    return json.loads(response.content)

def parse_air_quality_data(data):
    items = data.get('response', {}).get('body', {}).get('items', [])
    air_quality_info = []
    for item in items:
        info = {
            '측정소명': item.get('stationName', 'N/A'),
            '날짜': item.get('dataTime', 'N/A'),
            'pm10농도': item.get('pm10Value', 'N/A'),
            'pm25농도': item.get('pm25Value', 'N/A'),
            '통합대기환경수치': item.get('khaiValue', 'N/A'),
        }
        air_quality_info.append(info)
    return air_quality_info

def main():
    st.title("대기질 정보 제공 챗봇")

    # 지역 목록
    sido_options = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기도", "강원도", "충청북도", "충청남도", "전라북도", "전라남도", "경상북도", "경상남도", "제주도"]
    selected_sido = st.selectbox("대기질 정보를 알고 싶은 지역을 선택하세요:", sido_options)

    # 해당 지역의 대기질 정보 쿼리
    result = seoul_pm_query(selected_sido, key)
    if result:
        air_quality_info = parse_air_quality_data(result)

        documents = [
            Document(page_content=", ".join([f"{key}: {str(info[key])}" for key in ['측정소명', '날짜', 'pm10농도', 'pm25농도', '통합대기환경수치']]))
            for info in air_quality_info
        ]

        embedding_function = SentenceTransformerEmbeddings(model_name="jhgan/ko-sroberta-multitask")
        db = FAISS.from_documents(documents, embedding_function)

        retriever = db.as_retriever(search_type="similarity", search_kwargs={'k': 5, 'fetch_k': 100})

        # User query
        query = st.text_input("대기질에 대해 궁금한 점을 입력하세요:", "")
        if query:
            docs = retriever.get_relevant_documents(query)

            if docs:
                template = """
                너는 다방면에서 전문가야. 정확한 대답을 해줘.
                Answer the question as based only on the following context:
                {context}
                
                Question: {question}
                """
                
                prompt = ChatPromptTemplate.from_template(template)
                llm = ChatOllama(model="gemma2:9b", temperature=0, base_url="http://127.0.0.1:11434/")
                
                chain = RunnableMap({
                    "context": lambda x: retriever.get_relevant_documents(x['question']),
                    "question": lambda x: x['question']
                }) | prompt | llm
                
                result_content = chain.invoke({'question': query}).content
                st.markdown(result_content)
            else:
                st.error("관련된 대기질 정보를 찾을 수 없습니다.")

if __name__ == "__main__":
    main()
