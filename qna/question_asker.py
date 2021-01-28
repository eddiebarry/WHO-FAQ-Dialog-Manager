import sys
import json
import copy
from os import listdir
from os.path import join as os_path_join
from collections import defaultdict
from common import preprocess
from common import tokenize


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
    
    def __init__(self, config_path, show_options=False, qa_keyword_path=None,
        use_question_predicter_config=None):
        
        # Read the config file which specifies the questions that must
        # be cumpolsorily asked

        self.config_path=config_path
        self.config = {}
        for filename in listdir(self.config_path):
            if filename.endswith('.json'):                    
                project_id, version_id = filename.split('_')[:2]
                self.config[project_id] = self.config.setdefault(project_id, {})
                with open(os_path_join(self.config_path, filename), 'r') as f:
                    self.config[project_id][version_id] = json.load(f)

        self.show_options = show_options
        self.qa_keyword_path = qa_keyword_path
        if self.show_options and self.qa_keyword_path:
            self.config = self.add_options(
                config=self.config,
                qa_keyword_path=qa_keyword_path
            )
        
        # Tracking which questions are asked so as to not ask them again
        self.questions_asked = defaultdict(list)
        
        # Check wether questions must be predicted
        self.use_question_predicter = False
        self.question_predicter = None
        
        if use_question_predicter_config is not None:
            from question_predictor import QuestionPredicter
            self.use_question_predicter = use_question_predicter_config[0]
            if self.use_question_predicter:
                model_path=use_question_predicter_config[1]
                vectoriser_path=use_question_predicter_config[2]
                self.question_predicter = QuestionPredicter(\
                    model_path, vectoriser_path)

    def process(self, user_id, keywords, project_id, version_id, user_input=None):
        """
        Given a user ID, identifies which question must be asked,
        and adds them to what to say
        """
        # First we check if the user has already been asked a question
        if user_id in self.questions_asked.keys():
            must = self.questions_asked[user_id]
            # print("using previous config")
        else:
            # print(self.use_question_predicter, "is the use question prediction")
            if self.use_question_predicter:
                must = self.question_predicter.\
                    get_must_questions(user_input)
                # print("using predicted config")
            else:                    
                must = copy.deepcopy(self.config[project_id][version_id]["must"])                    
                # print("using default config")
            must.append("Catch All")

        self.questions_asked[user_id] = must
        # print("Questions that must be asked before keyword search are : ", must)

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
                if key in self.config[project_id][version_id]:
                    what_to_say_init = self.config[project_id][version_id][key][0]
                    what_to_say_options = self.config[project_id][version_id][key][1]
                else:
                    what_to_say_init = "We broke something that must never be broken"\
                        + "WHOA-Dialog-Manager/qna/question_asker.py, line 80"
                if key == "Catch All":
                    asking_catch_all = True
                    what_to_say_init = self.config[project_id][version_id][key]
                    what_to_say_options = "none, Yes"
                first_question =  (key == self.config[project_id][version_id]["must"][0] or first_question)
                ask_more_question = True
                must.remove(key)
                break
        
        #  Update so that question is not asked again
        self.questions_asked[user_id] = must
        # print("Questions that must be asked after keyword search are : ", must)
        
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

        # # If no more questions to be asked, remove all trace of user
        # if not ask_more_question:
        #     self.questions_asked.pop(user_id)

        return not ask_more_question, resp

    def add_options(self, config, qa_keyword_path):
        """
        Shows which options are possible to the end user
        """
        # loading all keyword dictionaries, for all the available project ids
        # and version ids, in addition to the default ones:
        temp = {}
        for filename in listdir(qa_keyword_path):
            if filename.endswith('.json'):
                project_id, version_id = filename.split('_')[:2]
                temp[project_id] = temp.setdefault(project_id, {})
                with open(os_path_join(qa_keyword_path, filename), 'r') as f:
                    temp[project_id][version_id] = json.load(f)

        # combining all keyword dictionaries to the configurations with the 
        # respective project ids and version ids, including the default ones:
        for project_id in config.keys():
            for version_id in config[project_id].keys():

                for key in temp[project_id][version_id].keys():
                    if key in config[project_id][version_id].keys():
                        new_option = config[project_id][version_id][key] 
                    else:
                        new_option = "what is the " + key + "?"  
                    extra_option = "none, "
                    for token in temp[project_id][version_id][key]:
                        extra_option += token + ", "
                    extra_option = extra_option.strip().strip(',')
                    config[project_id][version_id][key] = [new_option, extra_option]

        return config


if __name__ == '__main__':
    # Do not add options

    # definition of variables for different test cases:

    test_configs = {
        0: {
            "must" :["Subject 2 - Vaccination / General", "Vaccine", \
                "Who is writing this"],
            "Subject 2 - Vaccination / General" : \
                "What topic is this most related to ?",
            "Vaccine" : "What vaccine are you talking about ?",
            "Who is writing this" : "For whom is this question being asked ?",
            "Catch All": "Is there any additional information you could help us with ?"
        },
        1: {
            "must" :["Subject 2 - Vaccination / General", "Vaccine", \
                "Who is writing this"],
            "Subject 2 - Vaccination / General" : \
                "What topic is this most related to ?",
            "Vaccine" : "What vaccine are you talking about ?",
            "Who is writing this" : "For whom is this question being asked ?",
            "Catch All": "Is there any additional information you could help us with ?"
        },
        2: {
            "must" :["Subject 2 - Vaccination / General", "Vaccine", \
                "Who is writing this"],
            "Subject 2 - Vaccination / General" : \
                "What topic is this most related to ?",
            "Vaccine" : "What vaccine are you talking about ?",
            "Who is writing this" : "For whom is this question being asked ?",
            "Catch All": "Is there any additional information you could help us with ?"
        }
    }
    test_qa_config_paths = {
        0: '../../data/question_asker_config_for_unit_tests',
        1: '../../data/question_asker_config_for_unit_tests',
        2: '../../data/question_asker_config_for_unit_tests'
    }
    test_queries = {
        0: "Is it safe for my child to get Pneumonia ?",
        1: "Is it safe for my child to get Polio ?",
        2: "Is it safe for my child to get Polio ?"
    }
    test_boosting_token_dicts = {
        0: {
            "keywords":["love"],    
            "subject1":["care"]
        },
        1: {
            "keywords":["love"],    
            "subject1":["care"]
        },
        2: {
            "Subject 2 - Vaccination / General":["safety"],    
            "Vaccine":["polio"],
            "Who is writing this":["child"],
        }
    }
    test_show_options = {
        0: False,
        1: True,
        2: True
    }
    test_qa_keyword_paths = {
        0: None,
        1: '../../data/unique_keywords',
        2: '../../data/unique_keywords'
    }
    test_question_predicter_configs = {
        0: None,
        1: [
            False,               #use question predicter
            "./models.txt",     #model path
            "./vectoriser.txt"  #vectoriser path
        ],
        2: [
            True,               #use question predicter
            "./models.txt",     #model path
            "./vectoriser.txt"  #vectoriser path
        ]
    }
    test_user_ids = {
        0: 1,
        1: 2,
        2: 3
    }
    test_project_ids = {
        0: '999',
        1: '999',
        2: '999'
    }
    test_version_ids = {
        0: '0',
        1: '0',
        2: '0'
    }

    assert test_configs.keys() == test_qa_config_paths.keys() == \
        test_queries.keys() == test_boosting_token_dicts.keys() == \
        test_show_options.keys() == test_qa_keyword_paths.keys() == \
        test_question_predicter_configs.keys() == test_user_ids.keys() == \
        test_project_ids.keys() == test_version_ids.keys()

    # for each unit test:
    for exampe_id in test_configs.keys():

        print('-' * 12, 'test n.', str(exampe_id), '-' * 12)

        # variables for the considered test:

        config = test_configs[exampe_id]
        qa_config_path = test_qa_config_paths[exampe_id]
        query = test_queries[exampe_id]
        boosting_tokens = test_boosting_token_dicts[exampe_id]
        show_options = test_show_options[exampe_id]
        extractor_json_path = test_qa_keyword_paths[exampe_id]
        use_question_predicter_config = \
            test_question_predicter_configs[exampe_id]
        user_id = test_user_ids[exampe_id]
        project_id = test_project_ids[exampe_id]
        version_id = test_version_ids[exampe_id]

        # writing test 

        filename = project_id + '_' + version_id + '_' + 'unit_test_config.json'
        with open(os_path_join(qa_config_path, filename), 'w')\
            as f:
            json.dump(config, f, indent=4)

        QAsker = QuestionAsker(
            config_path=qa_config_path,
            show_options=show_options,
            qa_keyword_path=extractor_json_path,
            use_question_predicter_config=use_question_predicter_config
        )

        print(
            'result:\n',
            QAsker.process(
                user_id=user_id,
                keywords=boosting_tokens,
                project_id=project_id,
                version_id=version_id,
                user_input=query
            )
        )

    print('-' * 12, 'end of tests', '-' * 12)

######################################################################################################
######################################################################################################
######################################################################################################
######################################################################################################
######################################################################################################
######################################################################################################


    # # Set up a configuration of which fields must be included
    # # Along with what to say when no keyword from the field is detected
    # config = {
    #     "must" :["Subject 2 - Vaccination / General", "Vaccine", \
    #         "Who is writing this"],
    #     "Subject 2 - Vaccination / General" : \
    #         "What topic is this most related to ?",
    #     "Vaccine" : "What vaccine are you talking about ?",
    #     "Who is writing this" : "For whom is this question being asked ?",
    #     "Catch All": "Is there any additional information you could help us with ?"
    # }

    # with open('./question_asker_config.json', \
    #     'w') as json_file:
    #     json.dump(config, json_file, indent=4) 
    
    # query = "Is it safe for my child to get Pneumonia ?"
    # boosting_tokens = {
    #                 "keywords":["love"],    
    #                 "subject1":["care"]
    #             }

    # qa_config_path = "./question_asker_config"
    # QAsker = QuestionAsker(qa_config_path)
    # print(QAsker.process(1,boosting_tokens,query))
    # # Add options

    # query = "Is it safe for my child to get Polio ?"
    # print("This is the predicted questions")
    # extractor_json_path = \
    #     "../../WHO-FAQ-Keyword-Engine/keyword_config/curated_keywords_1500.json"
    
    # use_question_predicter_config = [
    #         True,               #use question predicter
    #         "./models.txt",     #model path
    #         "./vectoriser.txt"  #vectoriser path
    #     ]
    # QAsker = QuestionAsker(qa_config_path, show_options=True, \
    #     qa_keyword_path = extractor_json_path, \
    #     use_question_predicter_config=use_question_predicter_config)
    # print(QAsker.process(2,boosting_tokens,query))

    # # Write test for catch all
    # print('$'*80)
    # print("This is the catch all")
    # config = {
    #     "must" :["Subject 2 - Vaccination / General", "Vaccine", \
    #         "Who is writing this"],
    #     "Subject 2 - Vaccination / General" : \
    #         "What topic is this most related to ?",
    #     "Vaccine" : "What vaccine are you talking about ?",
    #     "Who is writing this" : "For whom is this question being asked ?",
    #     "Catch All": "Is there any additional information you could help us with ?"
    # }
    # qa_config_path = "./question_asker_test_config.json"

    # with open(qa_config_path, \
    #     'w') as json_file:
    #     json.dump(config, json_file, indent=4) 
    
    # query = "Is it safe for my child to get Polio ?"
    # extractor_json_path = \
    #     "../../WHO-FAQ-Keyword-Engine/keyword_config/curated_keywords_1500.json"
    
    # use_question_predicter_config = [
    #         False,               #use question predicter
    #         "./models.txt",     #model path
    #         "./vectoriser.txt"  #vectoriser path
    #     ]

    # boosting_tokens = {
    #                 "Subject 2 - Vaccination / General":["safety"],    
    #                 "Vaccine":["polio"],
    #                 "Who is writing this":["child"],
    #             }

    # qa_config_path = "./question_asker_test_config"
    # extractor_json_path = \
    #     "../../WHO-FAQ-Keyword-Engine/keyword_config"

    # QAsker = QuestionAsker(qa_config_path, show_options=True, \
    #     qa_keyword_path = extractor_json_path, \
    #     use_question_predicter_config=use_question_predicter_config)
    
    # print("This is the predicted questions")
    # print(QAsker.process(3,boosting_tokens,query))
