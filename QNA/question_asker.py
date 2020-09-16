import sys
import json
from collections import defaultdict
from .question_predictor import QuestionPredicter

class QuestionAsker:
    """
    Question asker is the class, which given a config file,
    and detected keywords for a particular question, will predict the 
    next question we want to ask the user

    #TODO: Add atributes and methods
    """
    def __init__(self, config_path, show_options=False, \
        qa_keyword_path=None, use_question_predicter=False):
        f = open(config_path,)
        self.config = json.load(f)
        f.close()

        if show_options and qa_keyword_path:
            self.config = self.add_options(self.config, qa_keyword_path)
        
        # Tracking which questions are asked so as to not ask them again
        self.questions_asked = defaultdict(list)
        
        # Check wether questions must be predicted
        self.use_question_predicter = use_question_predicter
        self.question_predicter = None
        if self.use_question_predicter:
            self.question_predicter = QuestionPredicter()

    
    # TODO : Dont Ask questions which have already been asked
    def process(self, user_id, keywords, user_input=None):
        """
        Given a user ID, identifies which question must be asked,
        and adds them to what to say
        """
        # First we check if the user has already been asked a question
        if user_id in self.questions_asked.keys():
            must = self.questions_asked[user_id]
        else:
            if self.use_question_predicter:
                must = self.question_predicter.\
                    get_must_questions(user_input)
            else:
                must = self.config["must"]

        self.questions_asked[user_id] = must

        # check if all keywords in must are present in the keywords that 
        # are detected so far
        ask_more_question = False
        what_to_say = ""

        for key in must:
            if key not in keywords:
                what_to_say = self.config[key]
                ask_more_question = True
                must.remove(key)
                break
        
        #  Update so that question is not asked again
        self.questions_asked[user_id] = must
        

        # if not satisfied, add question in response
        resp = {
            "ask_more_question": ask_more_question,
            "what_to_say": what_to_say,
            "user_id": user_id,
        }

        return not ask_more_question, resp

    def add_options(self, config, qa_keyword_path):
        """
        Shows which options are possible to the end user
        """
        f = open(qa_keyword_path,)
        jsonObj = json.load(f)
        
        for key in config.keys():
            if key == "must":
                continue
            new_option = config[key] + "\nYour options are : \n"
            if key in jsonObj.keys():
                for token in jsonObj[key]:
                    new_option += token + ", "
            config[key] = new_option.strip().strip(',')
        
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
        "Who is writing this" : "For whom is this question being asked ?"
    }

    with open('./WHO-FAQ-Dialog-Manager/QNA/question_asker_config.json', \
        'w') as json_file:
        json.dump(config, json_file, indent=4) 
    
    query = "Is it safe for my child to get Pneumonia ?"
    boosting_tokens = {
                    "keywords":["love"],    
                    "subject1":["care"]
                }

    qa_config_path = "./WHO-FAQ-Dialog-Manager/QNA/question_asker_config.json"
    QAsker = QuestionAsker(qa_config_path)

    print(QAsker.process(query, 1,boosting_tokens))

    # Add options
