import sys
import json
import copy
from collections import defaultdict
from common import preprocess
from common import tokenize
from question_predictor import QuestionPredicter

class QuestionAsker:
    """
    Question asker is the class, which given a config file,
    and detected keywords for a particular question, will predict the 
    next question we want to ask the user

    Attributes
    ----------
    config_path : String
        A Lucene Analyzer for preprocessing text data

    Methods
    -------
    """
    
    def __init__(self, config_path, show_options=False, \
        qa_keyword_path=None, \
        use_question_predicter_config=None):
        
        # Read the config file which specifies the questions that must
        # be cumpolsorily asked
        self.config_path=config_path
        f = open(self.config_path,)
        self.config = json.load(f)
        f.close()

        self.show_options = show_options
        self.qa_keyword_path = qa_keyword_path
        if self.show_options and self.qa_keyword_path:
            self.config = self.add_options(self.config, qa_keyword_path)
        
        # Tracking which questions are asked so as to not ask them again
        self.questions_asked = defaultdict(list)
        
        # Check wether questions must be predicted
        self.use_question_predicter = False
        self.question_predicter = None
        
        if use_question_predicter_config is not None:
            self.use_question_predicter = use_question_predicter_config[0]
            model_path=use_question_predicter_config[1]
            vectoriser_path=use_question_predicter_config[2]
            self.question_predicter = QuestionPredicter(\
                model_path, vectoriser_path)

    def process(self, user_id, keywords, user_input=None):
        """
        Given a user ID, identifies which question must be asked,
        and adds them to what to say
        """
        # First we check if the user has already been asked a question
        if user_id in self.questions_asked.keys():
            must = self.questions_asked[user_id]
            print("using previous config")
        else:
            print(self.use_question_predicter, "is the use question prediction")
            if self.use_question_predicter:
                must = self.question_predicter.\
                    get_must_questions(user_input)
                print("using predicted config")
            else:
                must = copy.deepcopy(self.config["must"])
                print("using default config")
            must.append("Catch All")

        self.questions_asked[user_id] = must
        print("Questions that must be asked before keyword search are : ", must)

        # check if all keywords in must are present in the keywords that 
        # are detected so far
        ask_more_question = False
        what_to_say_init = ""
        what_to_say_options = ""

        for key in keywords:
            if key in must:
                must.remove(key)

        asking_catch_all = False
        first_question   = False
        for key in must:
            if key not in keywords:
                if key == "Catch All" and len(must)>1:
                    continue

                if key in self.config:
                    what_to_say_init = self.config[key][0]
                    what_to_say_options = self.config[key][1]
                else:
                    what_to_say_init = "We broke something that must never be broken"\
                        + "WHOA-Dialog-Manager/qna/question_asker.py, line 80"
                if key == "Catch All":
                    asking_catch_all = True
                    what_to_say_init = self.config[key]
                    what_to_say_options = "none, Yes"

                first_question =  (key == self.config["must"][0] or first_question)
                ask_more_question = True
                must.remove(key)
                break
        
        #  Update so that question is not asked again
        self.questions_asked[user_id] = must
        print("Questions that must be asked after keyword search are : ", must)
        
        # if not satisfied, add question in response
        resp = {
            "ask_more_question": ask_more_question,
            "what_to_say": {
                "heading": what_to_say_init,
                "options": what_to_say_options,
            },
            "user_id": user_id,
            "ask_catch_all": asking_catch_all,
            "first_question": first_question
        }

        # split into options
        for idx,x in enumerate(what_to_say_options.split(',')):
            new_title = "option_"+str(idx)
            resp['what_to_say'][new_title] = x.strip()

        # If no more questions to be asked, remove all trace of user
        if not ask_more_question:
            self.questions_asked.pop(user_id)

        return not ask_more_question, resp

    def add_options(self, config, qa_keyword_path):
        """
        Shows which options are possible to the end user
        """
        f = open(qa_keyword_path,)
        jsonObj = json.load(f)
        
        for key in jsonObj.keys():
            if key in config.keys():
                new_option = config[key] 
            else:
                new_option = "what is the " + key + "?"  
            # new_option += "\nYour options are : \n"

            extra_option = "none, "
            for token in jsonObj[key]:
                extra_option += token + ", "
            extra_option = extra_option.strip().strip(',')
            config[key] = [new_option, extra_option]

        return config


if __name__ == '__main__':
    # Do not add options

    # Set up a configuration of which fields must be included
    # Along with what to say when no keyword from the field is detected
    config = {
        "must" :["Subject 2 - Vaccination / General", "Vaccine", \
            "Who is writing this"],
        "Subject 2 - Vaccination / General" : \
            "What topic is this most related to ?",
        "Vaccine" : "What vaccine are you talking about ?",
        "Who is writing this" : "For whom is this question being asked ?",
        "Catch All": "Is there any additional information you could help us with ?"
    }

    with open('./question_asker_config.json', \
        'w') as json_file:
        json.dump(config, json_file, indent=4) 
    
    query = "Is it safe for my child to get Pneumonia ?"
    boosting_tokens = {
                    "keywords":["love"],    
                    "subject1":["care"]
                }

    qa_config_path = "./question_asker_config.json"
    QAsker = QuestionAsker(qa_config_path)
    print(QAsker.process(1,boosting_tokens,query))
    # Add options

    query = "Is it safe for my child to get Polio ?"
    print("This is the predicted questions")
    extractor_json_path = \
        "../../WHO-FAQ-Keyword-Engine/keyword_config/curated_keywords_1500.json"
    
    use_question_predicter_config = [
            True,               #use question predicter
            "./models.txt",     #model path
            "./vectoriser.txt"  #vectoriser path
        ]
    QAsker = QuestionAsker(qa_config_path, show_options=True, \
        qa_keyword_path = extractor_json_path, \
        use_question_predicter_config=use_question_predicter_config)
    print(QAsker.process(2,boosting_tokens,query))

    # Write test for catch all
    print('$'*80)
    print("This is the catch all")
    config = {
        "must" :["Subject 2 - Vaccination / General", "Vaccine", \
            "Who is writing this"],
        "Subject 2 - Vaccination / General" : \
            "What topic is this most related to ?",
        "Vaccine" : "What vaccine are you talking about ?",
        "Who is writing this" : "For whom is this question being asked ?",
        "Catch All": "Is there any additional information you could help us with ?"
    }
    qa_config_path = "./question_asker_test_config.json"

    with open(qa_config_path, \
        'w') as json_file:
        json.dump(config, json_file, indent=4) 
    
    query = "Is it safe for my child to get Polio ?"
    extractor_json_path = \
        "../../WHO-FAQ-Keyword-Engine/keyword_config/curated_keywords_1500.json"
    
    use_question_predicter_config = [
            False,               #use question predicter
            "./models.txt",     #model path
            "./vectoriser.txt"  #vectoriser path
        ]

    boosting_tokens = {
                    "Subject 2 - Vaccination / General":["safety"],    
                    "Vaccine":["polio"],
                    "Who is writing this":["child"],
                }

    QAsker = QuestionAsker(qa_config_path, show_options=True, \
        qa_keyword_path = extractor_json_path, \
        use_question_predicter_config=use_question_predicter_config)
    
    print("This is the predicted questions")
    print(QAsker.process(3,boosting_tokens,query))
