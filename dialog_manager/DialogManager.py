from DialogNodes import *
from params import *
import pandas as pd
import sys
sys.path.append('../')
from GigaChat import GigaChat
import regex as re
import tqdm
import json
import pprint
import chromadb
import os
import dotenv
import copy


class DialogSession:
    def __init__(self, dialog_tree, user_id):
        self.data = {}
        self.history = []
        self.dialog_tree = dialog_tree
        self.last_state = copy.copy(dialog_tree)
        self.user_id = user_id
                
    def send_msg(self, user_msg):
        if self.last_state is None:
            self.last_state = copy.copy(self.dialog_tree)
        node = self.last_state
            
        self.history.append({"user_type": "user", "msg": user_msg})
        self.get_last_n_message()
        req_answer = ''
        
        while node is not None and req_answer=='':    
            node_type = type(node)
            node_data = node.run(self.data)
            print(f"{node}: {node_data}")

            if node_type in [LLM_Generator, Dim_Search_Land]:
                req_answer = node_data['req_answer']
                self.history.append({"user_type": "ai", "msg": req_answer})
            if node_type == LLM_Extractor:
                for k, v in node_data['json_entites'].items():
                    self.data[k] = v
            if node_type == RAG_Classifier:
                for k, v in node_data['json_entites'].items():
                    self.data[k] = v

            node = node_data['child_node']
            self.last_state = node
        
        return req_answer
        
    def get_last_n_message(self, n_last=3):
        last_slice_msg = ''
        for i in self.history[-2*n_last:]:
            if i['user_type'] == 'user':
                last_slice_msg += i['msg'] + '\n'
        
        self.data['last_msg'] = last_slice_msg
        