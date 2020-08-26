import sys
import json


class QuestionAsker:
    def __init__(self, config_path):
        f = open(config_path,)
        self.config = json.load(f)
        f.close()
    
    def process(self, user_id, keywords):
        # check if satsified
        ask_more_question = False
        what_to_say = ""
        
        for key in self.config["must"]:
            if key not in keywords:
                what_to_say = self.config[key]
                ask_more_question = True
                break

        # if not satisfied, add question in response
        resp = {
            "ask_more_question": ask_more_question,
            "what_to_say": what_to_say,
            "user_id": user_id,
        }

        return not ask_more_question, resp


if __name__ == '__main__':
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
    
    print(QuestionAsker.process(query, boosting_tokens))