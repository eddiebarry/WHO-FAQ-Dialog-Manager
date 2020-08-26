import sys
import json


class QuestionAsker:
    def __init__(self, config_path):
        f = open(config_path,)
        self.config = json.load(f)
        f.close()
    
    def process(self, query, keywords):
        # check if satsified

        # if not satisfied, add question in response
        pass


if __name__ == '__main__':
    query = "Is it safe for my child to get Pneumonia ?"
    boosting_tokens = {
                    "keywords":["love"],    
                    "subject1":["care"]
                }

    qa_config_path = "./WHO-FAQ-Dialog-Manager/QNA/question_asker_config.json"
    QAsker = QuestionAsker(qa_config_path)
    
    QuestionAsker.process(query, boosting_tokens)