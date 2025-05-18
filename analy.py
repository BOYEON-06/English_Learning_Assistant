import spacy
from collections import defaultdict
import networkx as nx
from spacy.matcher import Matcher
import re

def load_nlp_model(lang="en"):
    """언어 모델 로드"""
    try:
        if lang == "en":
            return spacy.load("en_core_web_lg")
        else:
            return spacy.load(f"{lang}_core_web_sm")
    except OSError:
        print(f"{lang} 모델이 설치되어 있지 않습니다. 영어 모델을 사용합니다.")
        return spacy.load("en_core_web_sm")

class ClauseNode:
    """절 노드 클래스"""
    def __init__(self, start_idx, end_idx, text, clause_type, main_verb=None, subject=None):
        self.start_idx = start_idx
        self.end_idx = end_idx
        self.text = text
        self.type = clause_type
        self.main_verb = main_verb
        self.subject = subject
        self.parent = None
        self.children = []
        self.depth = 0
        self.role = None
        self.connector = None

class EnhancedClauseParser:
    """향상된 절 구조 파서"""
    
    def __init__(self, nlp):
        self.nlp = nlp
        self.matcher = Matcher(nlp.vocab)
        self._setup_patterns()
        self.clause_types = {
            "relative": ["who", "whom", "whose", "which", "that"],
            "nominal": ["that", "what", "whatever", "whether", "if", "how"],
            "adverbial": ["because", "since", "as", "when", "while", "after", "before", 
                         "until", "till", "unless", "if", "though", "although", "even though"]
        }
        
    def _setup_patterns(self):
        """구동사 및 기타 구문 패턴 설정"""
        self.matcher.add("PHRASAL_VERB", [
            [{"POS": "VERB"}, {"DEP": "prt"}],
            [{"POS": "VERB"}, {"POS": "ADP", "OP": "+"}, {"POS": "PRON", "OP": "?"}],
            [{"POS": "VERB"}, {"POS": "ADP"}, {"POS": "DET", "OP": "?"}, {"POS": "NOUN"}]
        ])
        
        self.matcher.add("CLAUSE_BOUNDARY", [
            [{"DEP": "mark"}],
            [{"POS": "SCONJ"}],
            [{"TAG": "WDT"}],
            [{"TAG": "WP"}],
            [{"TAG": "WRB"}]
        ])
    
    def analyze_sentence(self, text):
        """문장 전체 분석"""
        doc = self.nlp(text)
        
        # 1. 절 구조 분석
        clause_tree = self.build_clause_tree(doc)
        
        # 2. 각 절 내에서 동사-명사구 관계 분석
        clause_verb_np_roles = self.analyze_verb_np_roles_by_clause(doc, clause_tree)
        
        # 3. 생략된 주어 및 접속 구조 분석
        implied_subjects = self.resolve_zero_pronouns(doc, clause_tree)
        coord_structures = self.identify_coordination(doc)
        
        return {
            "doc": doc,
            "clause_tree": clause_tree,
            "clause_verb_np_roles": clause_verb_np_roles,
            "implied_subjects": implied_subjects,
            "coord_structures": coord_structures
        }
    
    def identify_main_clauses(self, doc):
        """주절 식별"""
        root = None
        for token in doc:
            if token.dep_ == "ROOT":
                root = token
                break
        
        if not root:
            return []
        
        main_clause_tokens = [root] + list(self._get_clause_tokens(root))
        main_clause_indices = sorted([t.i for t in main_clause_tokens])
        
        main_clauses = []
        current_indices = []
        
        for i, idx in enumerate(main_clause_indices):
            if i > 0 and idx > main_clause_indices[i-1] + 1:
                if current_indices:
                    start_idx = min(current_indices)
                    end_idx = max(current_indices) + 1
                    main_clauses.append((start_idx, end_idx))
                current_indices = [idx]
            else:
                current_indices.append(idx)
        
        if current_indices:
            start_idx = min(current_indices)
            end_idx = max(current_indices) + 1
            main_clauses.append((start_idx, end_idx))
        
        return main_clauses
    
    def _get_clause_tokens(self, head_token):
        """특정 토큰에 직접 의존하는 모든 토큰 찾기 (재귀적)"""
        tokens = []
        for child in head_token.children:
            if child.dep_ not in {"mark", "relcl", "advcl", "ccomp", "xcomp", "acl"}:
                tokens.append(child)
                tokens.extend(self._get_clause_tokens(child))
        return tokens
    
    def identify_subordinate_clauses(self, doc):
        """종속절 식별"""
        subordinate_clauses = []
        
        for token in doc:
            if token.dep_ in {"relcl", "advcl", "ccomp", "xcomp", "acl"}:
                clause_tokens = [token] + list(self._get_clause_tokens(token))
                clause_indices = sorted([t.i for t in clause_tokens])
                
                if clause_indices:
                    start_idx = min(clause_indices)
                    end_idx = max(clause_indices) + 1
                    
                    clause_type = "unknown"
                    if token.dep_ == "relcl":
                        clause_type = "relative"
                    elif token.dep_ == "advcl":
                        clause_type = "adverbial"
                    elif token.dep_ in {"ccomp", "xcomp"}:
                        clause_type = "nominal"
                    elif token.dep_ == "acl":
                        clause_type = "adjectival"
                    
                    connector = None
                    for child in token.children:
                        if child.dep_ == "mark" or child.pos_ in {"SCONJ", "CCONJ"} or child.tag_ in {"WDT", "WP", "WRB"}:
                            connector = child
                            break
                    
                    subordinate_clauses.append({
                        "start": start_idx,
                        "end": end_idx,
                        "head": token,
                        "type": clause_type,
                        "connector": connector,
                        "parent_idx": token.head.i if token.head != token else None
                    })
        
        return subordinate_clauses
    
    def build_clause_tree(self, doc):
        """문장의 절 구조 트리 구축"""
        main_clauses_indices = self.identify_main_clauses(doc)
        subordinate_clauses = self.identify_subordinate_clauses(doc)
        
        all_clauses = []
        
        # 주절 추가
        for start, end in main_clauses_indices:
            main_verb = None
            for token in doc[start:end]:
                if token.dep_ == "ROOT" or (token.pos_ == "VERB" and token.dep_ in {"ROOT", "ccomp", "xcomp"}):
                    main_verb = token
                    break
            
            subject = None
            if main_verb:
                for child in main_verb.children:
                    if child.dep_ in {"nsubj", "nsubjpass"}:
                        subject = child
                        break
            
            clause = ClauseNode(
                start_idx=start,
                end_idx=end,
                text=doc[start:end].text,
                clause_type="main",
                main_verb=main_verb,
                subject=subject
            )
            clause.role = "main"
            all_clauses.append(clause)
        
        # 종속절 추가
        for sc in subordinate_clauses:
            main_verb = sc["head"] if sc["head"].pos_ == "VERB" else None
            if not main_verb:
                for token in doc[sc["start"]:sc["end"]]:
                    if token.pos_ == "VERB" and token.head == sc["head"]:
                        main_verb = token
                        break
            
            subject = None
            if main_verb:
                for child in main_verb.children:
                    if child.dep_ in {"nsubj", "nsubjpass"}:
                        subject = child
                        break
            
            clause = ClauseNode(
                start_idx=sc["start"],
                end_idx=sc["end"],
                text=doc[sc["start"]:sc["end"]].text,
                clause_type=sc["type"],
                main_verb=main_verb,
                subject=subject
            )
            clause.connector = sc["connector"]
            
            if sc["type"] == "relative":
                clause.role = "relative_clause"
            elif sc["type"] == "adverbial":
                clause.role = "adverbial_clause"
            elif sc["type"] == "nominal":
                clause.role = "nominal_clause"
            elif sc["type"] == "adjectival":
                clause.role = "adjectival_clause"
            
            all_clauses.append(clause)
        
        # 절 간의 계층 구조 설정
        for clause in all_clauses:
            if clause.type == "main":
                continue
            
            parent_clause = None
            min_size = float('inf')
            
            for potential_parent in all_clauses:
                if potential_parent == clause:
                    continue
                
                if (potential_parent.start_idx <= clause.start_idx and 
                    potential_parent.end_idx >= clause.end_idx):
                    size = potential_parent.end_idx - potential_parent.start_idx
                    if size < min_size:
                        min_size = size
                        parent_clause = potential_parent
            
            if parent_clause:
                clause.parent = parent_clause
                parent_clause.children.append(clause)
        
        # 계층 깊이 설정
        for clause in all_clauses:
            depth = 0
            current = clause
            while current.parent:
                depth += 1
                current = current.parent
            clause.depth = depth
        
        return all_clauses
    
    def analyze_verb_np_roles_by_clause(self, doc, clause_tree):
        """각 절 내에서 동사-명사구 관계 분석"""
        clause_verb_np_roles = {}
        
        for clause in clause_tree:
            verb_np_roles = defaultdict(lambda: {
                'subject': [],
                'direct_object': [],
                'indirect_object': [],
                'others': []
            })
            
            # 명사구 식별 및 역할 파악
            for chunk in doc.noun_chunks:
                if not (clause.start_idx <= chunk.start < clause.end_idx):
                    continue
                
                head = chunk.root.head
                dep = chunk.root.dep_
                
                if head.pos_ in {"VERB", "AUX"}:
                    if dep in {"nsubj", "nsubjpass"}:
                        verb_np_roles[head]['subject'].append(chunk.text)
                    elif dep == "dobj":
                        verb_np_roles[head]['direct_object'].append(chunk.text)
                    elif dep == "iobj":
                        verb_np_roles[head]['indirect_object'].append(chunk.text)
                    elif dep == "pobj" and chunk.root.head.dep_ == "prep" and chunk.root.head.head == head:
                        if chunk.root.head.text.lower() in {"to", "for"}:
                            verb_np_roles[head]['indirect_object'].append(f"{chunk.root.head.text} {chunk.text}")
                        else:
                            verb_np_roles[head]['others'].append(f"{chunk.root.head.text} {chunk.text}")
                    else:
                        verb_np_roles[head]['others'].append(chunk.text)
            
            # 관계절 처리
            if clause.type == "relative" and clause.connector:
                rel_pronoun = clause.connector
                if clause.main_verb and rel_pronoun.text.lower() in {"who", "that", "which", "whom", "whose"}:
                    antecedent = None
                    if clause.parent:
                        for token in doc[clause.parent.start_idx:clause.parent.end_idx]:
                            if token.i == rel_pronoun.head.i:
                                antecedent = token.text
                                break
                    
                    if antecedent and rel_pronoun.dep_ == "nsubj":
                        verb_np_roles[clause.main_verb]['subject'].append(f"{antecedent} (as {rel_pronoun.text})")
                    elif antecedent and rel_pronoun.dep_ == "dobj":
                        verb_np_roles[clause.main_verb]['direct_object'].append(f"{antecedent} (as {rel_pronoun.text})")
            
            clause_verb_np_roles[clause] = dict(verb_np_roles)
        
        return clause_verb_np_roles
    
    def resolve_zero_pronouns(self, doc, clause_tree):
        """생략된 주어 추론"""
        implied_subjects = {}
        
        for clause in clause_tree:
            if clause.main_verb and not clause.subject:
                if clause.main_verb.tag_ == "VB" and clause.start_idx == 0:
                    implied_subjects[clause.main_verb] = "you (implied in imperative)"
                    continue
                
                if clause.parent and clause.parent.subject:
                    implied_subjects[clause.main_verb] = f"{clause.parent.subject.text} (implied from parent clause)"
        
        return implied_subjects
    
    def identify_coordination(self, doc):
        """접속 구조 식별"""
        coord_structures = []
        
        for token in doc:
            if token.dep_ == "conj" and token.head.pos_ == token.pos_:
                conjunction = None
                
                for sibling in token.head.children:
                    if sibling.dep_ == "cc" and sibling.i < token.i and sibling.i > token.head.i:
                        conjunction = sibling
                        break
                
                if not conjunction:
                    for i in range(token.head.i + 1, token.i):
                        if doc[i].text == ",":
                            conjunction = doc[i]
                            break
                
                coord_structures.append({
                    "type": token.pos_,
                    "first": token.head,
                    "conjunction": conjunction,
                    "second": token
                })
        
        return coord_structures