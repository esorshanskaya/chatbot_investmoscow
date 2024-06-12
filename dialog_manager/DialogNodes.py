from params import status_extractor_ok, status_extractor_not_found, default_child_key
import sys
sys.path.append("../")
import GigaChat
import traceback
import json
import pandas as pd

class Node():
    def __init__(self, gc: GigaChat, description = "", required_answer=False, key=""):
        self.gc = gc
        self.childs = {}
        self.description = description
        self.required_answer = required_answer
        self.key = key

    def _add_child(self, child, key):
        self.childs[key] = child

    def get_tree(self):
        tree = {self.description: {}}
        for k, v in self.childs.items():
            tree[self.description][k] = v.get_tree()
        return tree
    
    def print_tree(self):
        tree = self.get_tree()
        print(tree)
    
    def __repr__(self):
        return self.description
    
    # for dynamic rounting
    def update_system_prompt(self, system_prompt):
        self.system_prompt = system_prompt


# Нода для классификации 
class LLM_Classifier(Node):
    def __init__(self, gc, system_prompt=None, default_class=-1, description="", key="", required_answer=False):
        super().__init__(gc, description=description, key=key, required_answer=required_answer)
        self.system_prompt = system_prompt
        self._type = 'classifier'
        self.default_class = default_class

    def run(self, data):
        child_node = None
        req_class = None
        status = 0
        if self._type == 'classifier':
            req_class = self._classify_request(data[self.key])
            child_node = self.childs[req_class]
        return {"req_class": req_class, "child_node": child_node}
        
    def _classify_request(self, req):
        ans = self.gc.generate(system_prompt=self.system_prompt, 
                                    user_prompt=req)
        req_class = ans.replace("'", '').replace('"', '')[0]
        try:
            req_class = int(req_class)
        except:
            print('Paring error:', ans)
            req_class = self.default_class
        return req_class

    def add_child(self, child, class_):
        self._add_child(child, class_)


# Нода для генерации текста 
class LLM_Generator(Node):
    
    def __init__(self, gc=None, system_prompt=None, dummy_answer=None, description="", key="", required_answer=False):
        super().__init__(gc, description=description, key=key, required_answer=required_answer)
        self.system_prompt = system_prompt
        self._type = 'generator'
        self.dummy_answer=dummy_answer

    def run(self, data):
        child_node = None
        req_answer = self._generate_answer(data[self.key])
        child_node = self.childs.get(default_child_key, None)
        return {"req_answer": req_answer, "child_node": child_node}

    def _generate_answer(self, req):
        if not self.dummy_answer:
            ans = self.gc.generate(system_prompt=self.system_prompt, 
                                                    user_prompt=req)
        else:
            ans = self.dummy_answer
        return ans
    
    def add_child(self, child):
        if len(self.childs)==0:
            self._add_child(child, default_child_key)
        else:
            raise Exception("For generator node only 1 child allowed")


# Нода для вычления сущностей: 
class LLM_Extractor(Node):
    def __init__(self, gc, system_prompt=None, entity_list=[], description="", key="", required_answer=False):
        super().__init__(gc, description=description, key=key, required_answer=required_answer)
        self.system_prompt = system_prompt
        self._type = 'extractor'
        self.entity_list = entity_list

    def run(self, data):
        json_entites, status, unparsed_enities = self.extract(data[self.key])
        return {"json_entites": json_entites, "child_node": self.childs.get(status), 
                "status": status, "unparsed_enities": unparsed_enities}
        
    def extract(self, req):
        ans = self.gc.generate(system_prompt=self.system_prompt, user_prompt=req)
        unparsed_enities = []
        try:
            ans = json.loads(ans.replace("'", '"'))
        except Exception as e:
            print(f"Error on parsing: {ans}")
            print(traceback.format_exc())
            ans = {}
            status = status_extractor_not_found
            unparsed_enities = self.entity_list
            return ans, status, unparsed_enities
        unparsed_enities = list(set(self.entity_list) - set(ans.keys()))
        if len(unparsed_enities)==0:
            status = status_extractor_ok
        else:
            status = status_extractor_not_found
        return ans, status, unparsed_enities

    def add_child(self, child, status):
        self._add_child(child, status)
        

class RAG_Classifier(Node):
    def __init__(self, collection, gc, target_field, top_n=3, description="", key="", required_answer=False):
        super().__init__(gc, description=description, key=key, required_answer=required_answer)
        self.gc = gc
        self.collection = collection
        self.target_field = target_field
        self.top_n = top_n

    def run(self, data):
        df_search_res = self._search_top_result(data[self.key])
        top_result = self._get_top_result(df_search_res)
        child_node = self.childs.get(default_child_key, None)
        return {"json_entites": {self.key: top_result}, "child_node": child_node}

    def _search_top_result(self, req):
        query_embedding = self.gc.get_embedding(req)
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=10
        )
        for k in ['ids', 'distances', 'metadatas', 'documents']:
            results[k] = results[k][0]
        del results['uris'], results['data']
        results = pd.DataFrame(results)
        
        meta_keys = list(results['metadatas'].values[0].keys())
        results[meta_keys] = results['metadatas'].apply(pd.Series)
        results = results.drop(columns=['metadatas'])
        return results

    def _get_top_result(self, df_search_res):
        return list(df_search_res[self.target_field].value_counts().head(self.top_n).index)

    def add_child(self, child):
        self._add_child(child, default_child_key)



def get_dialog_tree(node_dict, gc):
    
    if node_dict['type']==LLM_Classifier:
        node = LLM_Classifier(gc=gc, 
                              system_prompt=node_dict.get('system_prompt'),
                              default_class=node_dict.get('default_class'),
                              key=node_dict.get('key'),
                              description=node_dict.get('description', None)
                             )
        
    elif node_dict['type']==LLM_Generator:
        node = LLM_Generator(gc=gc, 
                              system_prompt=node_dict.get('system_prompt', None),
                              dummy_answer=node_dict.get('dummy_answer', None),
                              key=node_dict.get('key'),
                              description=node_dict.get('description', None)
                            )
        
    elif node_dict['type']==LLM_Extractor:
        node = LLM_Extractor(gc=gc, 
                             system_prompt=node_dict.get('system_prompt'),
                             entity_list=node_dict.get('entity_list', []),
                             key=node_dict.get('key'),
                             description=node_dict.get('description', None)
                            )
    elif node_dict['type']==RAG_Classifier:
        node = RAG_Classifier(gc=gc,
                             collection=node_dict.get('collection'),
                             target_field=node_dict.get('target_field'),
                             top_n=node_dict.get('top_n'),
                             key=node_dict.get('key'),
                             description=node_dict.get('description'))
    else:
        raise Exception(f"Unknown type of Node: {type(node_dict['type'])}")
        
    if node_dict['type'] in [LLM_Classifier, LLM_Extractor]:
        for child_key, child_node_dict in node_dict['childs'].items():
            child_node = get_dialog_tree(child_node_dict, gc=gc)
            node.add_child(child_node, child_key)
    else:
        for _, child_node_dict in node_dict['childs'].items():
            child_node = get_dialog_tree(child_node_dict, gc=gc)
            node.add_child(child_node)

    return node