import os
import string
import random
import numpy as np
import scipy.sparse as sp
import pandas as pd
from csv import reader

import nltk
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context
    
nltk.download('punkt')
nltk.download('stopwords')

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import ComplementNB

import sys
import json
from collections import defaultdict
from common import preprocess
from common import tokenize
import pickle



# TODO : Document
class QuestionPredicter:
    """
    Question predicter is the class that when given a user input,
    predicts which questions we must ask

    #TODO: Add atributes and methods
    """
    def __init__(self, class_dict_pth="/usr/src/WHOA-FAQ-Answer-Project/WHO-FAQ-Dialog-Manager/qna/models.txt", \
        vectoriser_pth="/usr/src/WHOA-FAQ-Answer-Project/WHO-FAQ-Dialog-Manager/qna/vectoriser.txt"):
        """
        Given a diction of keywords and corresponding classifiers
        which tell wether the keyword is necessary, we build a 
        set of questions that must be asked to the user
        """
        with open(class_dict_pth, 'rb') as f:
            self.class_dict = pickle.load(f)
        
        with open(vectoriser_pth, 'rb') as f:
            self.vectoriser = pickle.load(f)

    # TODO : Dont Ask questions which have already been asked
    def get_must_questions(self, user_input):
        """
        Given a user input identified which questions must be asked
        """
        inp = [user_input]
        model_inp = self.vectoriser.transform(inp)
        print(model_inp)

        must = []
        for key in self.class_dict:
            pred = self.class_dict[key].predict(model_inp)
            if pred == 1:
                must.append(key)
        
        return must



if __name__ == '__main__':
    qpred = QuestionPredicter()
    must = qpred.get_must_questions("Please save my child")
    print(must, 'all these questions must be asked')