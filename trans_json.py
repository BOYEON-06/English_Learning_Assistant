import json
from translate_ko import ko_trans_many
from collections import defaultdict
from analy import load_nlp_model, EnhancedClauseParser

def convert_to_json_format(analysis_results):
    """분석 결과를 JSON 형식으로 변환"""
    doc = analysis_results["doc"]

    clause_tree_json = []
    clause_id_map = {}

    # 절에 ID 할당
    for i, clause in enumerate(analysis_results["clause_tree"]):
        clause_id_map[clause] = i

    for clause in analysis_results["clause_tree"]:
        clause_info = {
            "id": clause_id_map[clause],
            "text": clause.text,
            "start_idx": clause.start_idx,
            "end_idx": clause.end_idx,
            "type": clause.type,
            "role": clause.role or "unknown",
            "depth": clause.depth,
            "parent_id": clause_id_map.get(clause.parent) if clause.parent else None,
            "children_ids": [clause_id_map[child] for child in clause.children],
            "main_verb": clause.main_verb.text if clause.main_verb else None,
            "subject": clause.subject.text if clause.subject else None,
            "connector": clause.connector.text if clause.connector else None
        }
        clause_tree_json.append(clause_info)

    verb_np_roles_json = {}
    for clause, verb_roles in analysis_results["clause_verb_np_roles"].items():
        clause_id = clause_id_map[clause]
        verb_np_roles_json[clause_id] = {}

        for verb, roles in verb_roles.items():
            verb_text = verb.text
            verb_np_roles_json[clause_id][verb_text] = {
                "subject": roles["subject"],
                "direct_object": roles["direct_object"],
                "indirect_object": roles["indirect_object"],
                "others": roles["others"]
            }

    implied_subjects_json = {}
    for verb, subject in analysis_results["implied_subjects"].items():
        implied_subjects_json[verb.text] = subject

    coord_structures_json = []
    for coord in analysis_results["coord_structures"]:
        coord_info = {
            "type": coord["type"],
            "first": coord["first"].text,
            "conjunction": coord["conjunction"].text if coord["conjunction"] else ",",
            "second": coord["second"].text
        }
        coord_structures_json.append(coord_info)

    result_json = {
        "sentence": doc.text,
        "clause_tree": clause_tree_json,
        "verb_np_roles": verb_np_roles_json,
        "implied_subjects": implied_subjects_json,
        "coord_structures": coord_structures_json
    }

    return result_json

def analyze_multiple_sentences(text, output_path="output.json"):
    """여러 문장을 분석하고 하나의 JSON 파일로 저장"""
    nlp = load_nlp_model("en")
    parser = EnhancedClauseParser(nlp)
    
    # 문장 분리
    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents]
    
    all_results = []

    # 문장별 한글 번역 수행
    cleaned_senteces = [sentence.replace('\n', ' ').strip() for sentence in sentences]

    print(cleaned_senteces)
    translated_sentences = ko_trans_many(cleaned_senteces)
    
    # 각 문장 분석
    for i, sentence in enumerate(sentences):
        try:
            analysis_results = parser.analyze_sentence(sentence)
            json_data = convert_to_json_format(analysis_results)
            
            # 문장 번호 추가
            json_data["sentence_number"] = i + 1
            json_data["translated"] = translated_sentences[i]
            
            all_results.append(json_data)
            print(f"✅ 문장 {i+1} 분석 완료")
            
        except Exception as e:
            print(f"⚠️ 문장 {i+1} 분석 중 오류 발생: {e}")
    
    # 최종 결과 저장
    final_result = {
        "total_sentences": len(sentences),
        "results": all_results
    }
    
    # with open(output_path, "w", encoding="utf-8") as f:
    #     json.dump(final_result, f, ensure_ascii=False, indent=2)
    
    # print(f"✅ 전체 분석 결과가 '{output_path}'에 저장되었습니다.")

    # 전체 변연 결과를 하나로 묶어서 반환 
    return final_result
    # return final_result 
    # /ko_trans_page 라우터로 이동
    # json파일(분석결과)를 DB 저장 후 바로 최종 UI 구현(spacy_result.html)과 이어지게 개발 예정

def spacy_trans(ocr_text, output_path="output.json"):
    return analyze_multiple_sentences(ocr_text, output_path)

# if __name__ == "__main__":

#     # def spacy_trans(ocr_text):
#     #     input_text = ocr_text
    
#     # 분석 및 저장
#     analyze_multiple_sentences(input_text, "all_sentences.json")