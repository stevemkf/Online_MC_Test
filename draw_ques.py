import pandas as pd
import openpyxl
import random

class DrawQuestions():

    def __init__(self):
        # Question group: M, N, O, P
        # Question category: A to H
        total_groups = 4
        total_cats = 8
        # Create a 2D question position list.  Position means Excel dataframe row number
        question_pos_lists = [[[] for col in range(total_cats)] for row in range(total_groups)]

        # Parse all rows in the question worksheet and fill in the 2D question position lists
        self.df = pd.read_excel("questions.xlsx", sheet_name="TTR")
        for index, row in self.df.iterrows():
            # question_num: e.g. M01A, P04H
            question_num = row['no']
            group = ord(question_num[0]) - ord('M')
            cat = ord(question_num[len(question_num) - 1]) - ord('A')
            question_pos_lists[group][cat].append(index)

        # Number of questions to be drawn from each category
        total_ques_cat = [10, 10, 10, 10, 15, 15, 15, 15]

        # Draw questions for a test paper
        self.ques_pos_paper = []
        # The questions will follow the category orders, i.e. A to H
        for index, num_ques_cat in enumerate(total_ques_cat):
            # Choose either Group M or N + either Group O or P for each category of questions
            group1 = random.randint(0, 1)
            group2 = random.randint(2, 3)
            cat_ques_pos = question_pos_lists[group1][index] + question_pos_lists[group2][index]
            ques_pos_drawn = random.sample(cat_ques_pos, num_ques_cat)
            # Sort the questions so that it is easier to check the results
            ques_pos_drawn.sort()
            # Combine the questions to form the test paper
            self.ques_pos_paper = self.ques_pos_paper + ques_pos_drawn

        self.total_ques_paper = len(self.ques_pos_paper)


    # Retrieve the question contents from dataframe, based on their position numbers
    def get_question(self, index):
        index_df = self.ques_pos_paper[index]
        row_content = self.df.iloc[index_df]
        d = dict()
        d["question_num"] = row_content['no']    # e.g. e.g. M01A, P04H
        d["question"] = row_content['question']
        d["choice_1"] = str(row_content['cho1'])
        d["choice_2"] = str(row_content['cho2'])
        d["choice_3"] = str(row_content['cho3'])
        d["choice_4"] = str(row_content['cho4'])
        d["answer"] = row_content['ans']
        image = row_content['pic']
        # empty cell return NaN which should be replaced with empty string
        if image != image:
            image = ""
        d["image"] = image
        return(d)

