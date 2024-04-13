import sqlite3
import openpyxl


# Create mark sheet as Excel file
def write_marksheet(marksheet):
    workbook = openpyxl.Workbook()
    # Select the default sheet (usually named 'Sheet')
    sheet = workbook.active
    for item in marksheet:
        sheet.append(item)
    workbook.save("scores.xlsx")


# retrieve candidates' data from SQLite3 database
connection = sqlite3.connect("instance/data.db")
cursor = connection.execute("SELECT id, candidate_no, last_name, first_name, correct_ans_str, ans_str from Candidates WHERE test_completed=True")

# computed scores will be written onto an Excel file, in addition to the database
marksheet = []
marksheet.append(['candidate no.', 'last name', 'first name', 'final score'])

score_id_list = []
record = cursor.fetchone()
while record is not None:
    id = record[0]
    candidate_no = record[1]
    last_name = record[2]
    first_name = record[3]
    # convert string to list in order to check the answers one by one
    correct_ans_list = [item for item in record[4].split(',')]
    ans_list = [item for item in record[5].split(',')]
    final_score = 0
    for index in range(0, len(correct_ans_list)):
        if ans_list[index] == correct_ans_list[index]:
            final_score = final_score + 1

    # build the score, id list so that SQL update will be executed faster
    score_id_list.append([final_score, id])
    # build the mark sheet
    marksheet.append([candidate_no, last_name, first_name, final_score])
    record = cursor.fetchone()

cursor.close()
connection.executemany("UPDATE Candidates SET final_score=? WHERE id=?", score_id_list)
connection.commit()
connection.close()
write_marksheet(marksheet)

