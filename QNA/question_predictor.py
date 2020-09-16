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
from nltk.tokenize import word_tokenize
from nltk.tokenize import RegexpTokenizer
from nltk.stem import PorterStemmer
from nltk.stem import SnowballStemmer
from nltk.corpus import stopwords
from sklearn.metrics import recall_score
from sklearn.metrics import precision_score
from sklearn.metrics import accuracy_score
from sklearn.metrics import f1_score
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import ComplementNB

import sys
import json
from collections import defaultdict
import pickle

# preprocessing step:
def preprocess(sentence):
    return sentence

porter_stemmer_instance = PorterStemmer()

# tokenization step:
def tokenize(preprocessed_sentence):
    # tokenizing sentence:
    token_list = []
    tokens = word_tokenize(preprocessed_sentence)
    for token in tokens:
        # stemming tokens:
        token = porter_stemmer_instance.stem(token)
        # stop-word and punctuation removal:
        if token not in stopwords.words('english') and token not in string.punctuation:
            token_list.append(token)
    return token_list

# TODO : Document
class QuestionPredicter:
    """
    Question predicter is the class that when given a user input,
    predicts which questions we must ask

    #TODO: Add atributes and methods
    """
    def __init__(self, class_dict_pth="./models.txt", \
        vectoriser_pth="./vectoriser.txt"):
        """
        Given a diction of keywords and corresponding classifiers
        which tell wether the keyword is necessary, we build a 
        set of questions that must be asked to the user
        """
        self.class_dict = pickle.load(open(class_dict_pth, 'rb'))
        self.vectoriser = pickle.load(open(vectoriser_pth,'rb'))

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