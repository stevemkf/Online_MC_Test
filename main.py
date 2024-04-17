from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from read_config import *
from draw_ques import DrawQuestions
from compute_scores import ComputeScores
import pandas as pd
import openpyxl


app = Flask(__name__)
app.config["SECRET_KEY"] = "there_is_no_secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
db = SQLAlchemy(app)
cs = ComputeScores(db)

# Carry out the preparation.  Questions will be drawn later.
ques_bank = DrawQuestions(file_ques_bank, first_group, last_group, first_category, last_category)


# define the structure of database table
class Candidates(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    batch_no = db.Column(db.Integer)
    candidate_no = db.Column(db.String(20))
    first_name = db.Column(db.String(40))
    last_name = db.Column(db.String(20))
    phone_no = db.Column(db.String(20))
    date_updated = db.Column(db.Date)
    time_updated = db.Column(db.Time)
    index_df_str = db.Column(db.String(1000))          # index_df: 0 to ...
    ques_num_str = db.Column(db.String(1000))          # ques_num: e.g. M01A
    correct_ans_str = db.Column(db.String(400))
    ans_str = db.Column(db.String(400))
    ques_no = db.Column(db.Integer)
    test_completed = db.Column(db.Boolean)
    final_score = db.Column(db.Integer)


# Log-in is required before proceeding to the MC test.
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        batch_no = request.form["batch_no"]
        session['batch_no'] = int(batch_no)
        candidate_no = request.form["candidate_no"]
        password = request.form["password"]

        # administrator?
        if (candidate_no == "admin") and (password == "39076670"):
            session['administrator'] = "Steve Fung"
            return redirect("/admin")

        # check if the candidate's test data exist in database
        cand_data = db.session.query(Candidates).filter_by(batch_no=batch_no, candidate_no=candidate_no).first()
        if cand_data is not None:
            # check password
            if password != cand_data.phone_no:
                flash("密碼不正確!", "error")
                flash("Incorrect password!", "error")
            # if the candidate has already completed the test (i.e. score >= 0),
            # he/she is not allowed to enter again
            elif cand_data.test_completed is True:
                flash("你的測驗已經結束!", "error")
                flash("You have already completed the test!", "error")
            else:
                # else, retrieve the data and keep them in session variables
                # this will avoid excessive access to database during the test
                session['candidate_no'] = candidate_no
                index_df_str = cand_data.index_df_str
                ans_str = cand_data.ans_str
                index_df_list = [int(item) for item in index_df_str.split(',')]
                ans_list = [item for item in ans_str.split(',')]
                session['ques_list'] = index_df_list
                session['ans_list'] = ans_list
                session['ques_no'] = cand_data.ques_no
                return redirect("/mc_test")
        else:
            flash("測驗編號或考生編號不正確!", "error")
            flash("Test batch no. or Candidate no. incorrect!", "error")
    return render_template("index.html")


# Let candidate answer the MC questions one by one
@app.route("/mc_test", methods=["GET", "POST"])
def mc_test():
    global ques_bank

    # if candidate has not yet logged in, direct to the log in page
    if not 'candidate_no' in session.keys():
        return redirect("/index")

    increment = 0

    if request.method == "POST":
        # save the answer just picked
        if "answer" in request.form:
            answer = request.form["answer"]
            session['ans_list'][session['ques_no'] - 1] = answer

        # save all answers entered up to this moment
        if "save" in request.form:
            # without the following line, session variable will not be updated with the picked answer
            session.modified = True
            return redirect("/save")

        # end of the test?
        if "finish" in request.form:
            # without the following line, session variable will not be updated with the picked answer
            session.modified = True
            return redirect("/finish")

        # the candidate is allowed to move forward or backward
        if "direction" in request.form:
            direction = request.form["direction"]
            if direction == "next":
                increment = 1
            elif direction == "prev":
                increment = -1

    # get the next/prev question
    ques_no = session['ques_no'] + increment
    total_ques = len(session['ques_list'])
    if ques_no > total_ques:
        ques_no = 1
    if ques_no == 0:
        ques_no = total_ques
    session['ques_no'] = ques_no

    index_df = session['ques_list'][ques_no - 1]
    ques = ques_bank.get_question(index_df)
    # remember those answers which have already been entered by the candidate
    exist_ans = session['ans_list'][ques_no - 1]

    # show the question and answers to the candidate through HTML
    return render_template("mc_test.html",
                           ques_num=session['ques_no'],
                           question=ques["question"],
                           choice_1=ques["choice_1"],
                           choice_2=ques["choice_2"],
                           choice_3=ques["choice_3"],
                           choice_4=ques["choice_4"],
                           fname_image=ques["image"],
                           exist_ans=exist_ans)


def update_ans(completed):
    # save candidate's answers into database
    batch_no = session["batch_no"]
    candidate_no = session["candidate_no"]
    ans_list = session['ans_list']
    ans_str = ",".join(item for item in ans_list)

    candidate = db.session.query(Candidates).filter_by(batch_no=batch_no, candidate_no=candidate_no).first()
    # answers cannot be changed if test has been completed before.
    if candidate.test_completed is True:
        return -1

    candidate.ans_str = ans_str
    # log the time and the current question no. as well
    today = date.today()
    t_now = datetime.now().time()
    candidate.date_updated = today
    candidate.time_updated = t_now
    candidate.ques_no = session['ques_no']
    candidate.test_completed = completed
    final_score = 0

    # if candidate has completed the whole test, calculate his/her final score
    if completed is True:
        correct_ans_list = [item for item in candidate.correct_ans_str.split(',')]
        for index in range(0, len(correct_ans_list)):
            if ans_list[index] == correct_ans_list[index]:
                final_score = final_score + 1
        candidate.final_score = final_score

    db.session.commit()
    return final_score


@app.route("/save")
def save():
    result = update_ans(completed=False)
    if result == -1:
        session.clear()
        message = f"測驗較早前已經結束，答案不能更改。<br>Test finished before.  Answers cannot be changed."
        return message
    else:
        flash("答案已經儲存至伺服器。", "success")
        flash("Your answers have been saved in server.", "success")
        return redirect("/mc_test")


@app.route("/finish")
def finish():
    result = update_ans(completed=True)
    if result == -1:
        message = f"測驗較早前已經結束，答案不能更改。<br>Test finished before.  Answers cannot be changed."
    else:
        message = f"測驗結束。 你的總分是 {result}.<br>Test finished. Your score is {result}."
    # clear the Session variables
    session.clear()
    return message


# Retrieve candidates' information from Excel file, then prepare records in database
def init_test_batch(batch_no):
    global ques_bank

    df = pd.read_excel(candidates_data)
    filtered_dt = df.query('batch_no == @batch_no')
    count = 0
    for index, row in filtered_dt.iterrows():
        candidate_no = row['cand_no']
        first_name = row['first_name']
        last_name = row['last_name']
        phone_no = str(row['phone_no'])
        # if candidate's record is not found in database, create one
        if db.session.query(Candidates).filter_by(batch_no=batch_no, candidate_no=candidate_no).first() is None:
            # draw one set of questions for each candidate
            index_df_list = ques_bank.get_ques_list(first_group, mid_group, last_group, ques_per_cat_list)
            ques_num_list, correct_ans_list = ques_bank.get_ques_num_ans_list(index_df_list)
            # convert Python list to delimited string or it could not be stored into database
            index_df_str = ",".join(str(item) for item in index_df_list)
            ques_num_str = ",".join(item for item in ques_num_list)
            correct_ans_str = ",".join(item for item in correct_ans_list)
            ans_list = ['0'] * len(index_df_list)
            ans_str = ",".join(item for item in ans_list)
            # indicate that the candidate has not yet attempted the test
            candidate = Candidates(batch_no=batch_no, candidate_no=candidate_no, first_name=first_name, last_name=last_name,
                                   phone_no=phone_no, index_df_str=index_df_str, ques_num_str=ques_num_str,
                                   correct_ans_str=correct_ans_str, ans_str=ans_str, ques_no=1, test_completed=False)
            db.session.add(candidate)
            db.session.commit()
            count = count + 1
    return count


@app.route("/admin", methods=["GET", "POST"])
def admin():

    # if administrator has not logged in, direct to the log-in page
    if not 'administrator' in session.keys():
        return redirect("/")
    if session['administrator'] != "Steve Fung":
        return redirect("/")

    batch_no = session['batch_no']                                    # for the first entry of this html page
    if request.method == "POST":
        batch_no = int(request.form["batch_no"])
        if "init" in request.form:
            count = init_test_batch(batch_no)
            flash(f"{count} records were newly added in the server.", "success")
        elif "show" in request.form:
            pass
        elif "terminate" in request.form:
            for candidate in db.session.query(Candidates).filter_by(batch_no=batch_no).all():
                candidate.test_completed = True
            db.session.commit()
            flash("Done.", "success")
        elif "compute" in request.form:
            cs.compute_scores(batch_no)
            flash("Scores were also exported to Excel file 'scores.xlsx'.", "success")
        elif "change" in request.form:
            candidate_no = request.form["candidate_no"]
            candidate = db.session.query(Candidates).filter_by(batch_no=batch_no, candidate_no=candidate_no).first()
            if candidate is not None:
                status = candidate.test_completed
                candidate.test_completed = 1 - status
                db.session.commit()
                flash(f"Status was changed.", "success")
            else:
                flash("Candidate no. not found.  Please check.", "success")
    # data will be a list of tuples
    data = db.session.query(Candidates.candidate_no, Candidates.last_name, Candidates.first_name,
                            Candidates.test_completed, Candidates.final_score).filter_by(batch_no=batch_no).all()
    heading = ("Candidate No.", "Last Name", "First Name", "Test Completed", "Score")
    return render_template("admin.html", batch_no=batch_no, headings=heading, data=data)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # add host IP in case you want multiple candidates to sit for the test on local network
        # run(debug=True, host='192.168.1.69', port=5001)
        app.run(debug=True, port=5001)