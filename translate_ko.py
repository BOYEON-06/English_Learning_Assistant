from libretranslatepy import LibreTranslateAPI
import requests

def ko_trans(text):
    # from app import get_ko_translated
    response = requests.post('http://localhost:5000/translate', data={
        "q": text,
        "source": "en",
        "target": "ko",
        "format": "text"
    })
    response.raise_for_status()
    return response.json()["translatedText"]

def ko_trans_many(sentences):
    # 여러 문장을 개별 번역해 리스트로 반환
    return [ko_trans(sentence) for sentence in sentences]