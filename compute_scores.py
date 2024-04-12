import sqlite3

connection = sqlite3.connect("instance/data.db")
cursor = connection.execute("SELECT id, candidate_no, correct_ans_str, ans_str from Candidates WHERE test_completed=True")

score_id_list = []
record = cursor.fetchone()
while record is not None:
    id = record[0]
    # convert string to list in order to check the answers one by one
    correct_ans_list = [item for item in record[2].split(',')]
    ans_list = [item for item in record[3].split(',')]
    final_score = 0
    for index in range(0, len(correct_ans_list)):
        if ans_list[index] == correct_ans_list[index]:
            final_score = final_score + 1
    # build the score, id list so that SQL update will be executed faster
    score_id_list.append([final_score, id])
    record = cursor.fetchone()

cursor.close()
connection.executemany("UPDATE Candidates SET final_score=? WHERE id=?", score_id_list)
connection.commit()
connection.close()
