import openpyxl
from read_config import file_scores


class ComputeScores():
    def __init__(self, db,):
        self.db = db


# Create mark sheet as Excel file
    def write_marksheet(self, marksheet):
        workbook = openpyxl.Workbook()
        # Select the default sheet (usually named 'Sheet')
        sheet = workbook.active
        for item in marksheet:
            sheet.append(item)
        workbook.save(file_scores)


    def compute_score(self, correct_ans_list, ans_list):
        final_score = 0
        for index in range(0, len(correct_ans_list)):
            if ans_list[index] == correct_ans_list[index]:
                final_score = final_score + 1
        return final_score


    def compute_scores(self, batch_no):
        # computed scores will be written onto an Excel file, in addition to the database
        marksheet = []
        marksheet.append(['batch no.', 'candidate no.', 'last name', 'first name', 'final score'])
        from main import Candidates
        for candidate in self.db.session.query(Candidates).filter_by(batch_no=batch_no, test_completed=True).all():
            id = candidate.id
            candidate_no = candidate.candidate_no
            last_name = candidate.last_name
            first_name = candidate.first_name
            correct_ans_str = candidate.correct_ans_str
            ans_str = candidate.ans_str
            # convert string to list in order to check the answers one by one
            correct_ans_list = [item for item in correct_ans_str.split(',')]
            ans_list = [item for item in ans_str.split(',')]
            final_score = self.compute_score(correct_ans_list, ans_list)
            candidate.final_score = final_score
            # build the mark sheet
            marksheet.append([batch_no, candidate_no, last_name, first_name, final_score])
        self.db.session.commit()
        self.write_marksheet(marksheet)













