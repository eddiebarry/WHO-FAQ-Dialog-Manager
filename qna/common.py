import string
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

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