from pathlib import Path
import pandas as pd
import openpyxl
from draw_ques import DrawQuestions


# Global variable storing trade specified configuration
config = {}
# Global variable storing trade specified dataframe
ques_bank = {}


# Parse configuration files and fill in the above two global variables
def create_trade_dicts():

    directory = "static/test_config"
    files = Path(directory).glob('config*.xlsx')

    for file in files:
        df = pd.read_excel(file, header=None)
        dict_trade = dict(zip(df[0], df[1]))

        trade = dict_trade['trade']
        file_ques_bank = dict_trade['question bank']
        first_group = dict_trade['first group']
        last_group = dict_trade['last group']
        first_category = dict_trade['first category']
        last_category = dict_trade['last category']
        # each trade contributes one entry in the dictionary
        ques_bank[trade] = DrawQuestions(f"static/questions/{file_ques_bank}",
                                         first_group, last_group, first_category, last_category)
        # again, each trade contributes one entry in the dictionary
        config[trade] = dict_trade




