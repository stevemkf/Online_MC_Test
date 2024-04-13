from flask import Flask, render_template, request, redirect, session, flash
from draw_ques import DrawQuestions
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import pandas as pd
import openpyxl
from read_config import *


app = Flask(__name__)
app.config["SECRET_KEY"] = "there_is_no_secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
db = SQLAlchemy(app)                        # Candidates' data will be saved onto database


# define the structure of database table
class Candidates(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    candidate_no = db.Column(db.String(20))
    first_name = db.Column(db.String(40))
    last_name = db.Column(db.String(20))
    phone_no = db.Column(db.String(20))
    date = db.Column(db.Date)
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
        candidate_no = request.form["candidate_no"]
        # check if the candidate's test data exist in database
        cand_data = db.session.query(Candidates).filter_by(candidate_no=candidate_no).first()
        if cand_data is not None:
            # if the candidate has already completed the test (i.e. score >= 0),
            # he/she is not allowed to enter again
            if cand_data.test_completed == True:
                flash("You have already completed the test !", "error")
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
                session['total_ques'] = len(index_df_list)
                session['ques_no'] = cand_data.ques_no
                return redirect("/mc_test")
        else:
            flash("考生編號不正確!", "error")
            flash("Candidate no. not found for this test session !", "error")
    return render_template("index.html")


# Let candidate answer the MC questions one by one
@app.route("/mc_test", methods=["GET", "POST"])
def mc_test():

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
    if ques_no > session['total_ques']:
        ques_no = 1
    if ques_no == 0:
        ques_no = session['total_ques']
    session['ques_no'] = ques_no

    index_df = session['ques_list'][ques_no - 1]
    ques = q.get_question(index_df)
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
    candidate_no = session["candidate_no"]
    ans_list = session['ans_list']
    ans_str = ",".join(item for item in ans_list)

    candidate = db.session.query(Candidates).filter_by(candidate_no=candidate_no).first()
    candidate.ans_str = ans_str

    # log the time and the current question no. as well
    t_now = datetime.now().time()
    candidate.time_updated = t_now
    candidate.ques_no = session['ques_no']

    # has the candidate completed the whole test?
    candidate.test_completed = completed
    db.session.commit()


@app.route("/save")
def save():
    update_ans(completed=False)
    flash("答案已經儲存至伺服器 Your answers have been saved in server.", "success")
    return redirect("/mc_test")


@app.route("/finish")
def finish():
    update_ans(completed=True)
    # clear the Session variables
    session.clear()
    return "<h1>測驗結束 Test finished!</h1>"


if __name__ == "__main__":
    with app.app_context():
        # Carry out the preparation.  Questions will be drawn later.
        q = DrawQuestions(file_ques_bank, first_group, last_group, first_category, last_category)
        db.create_all()
        # Retrieve candidates' information from Excel file, then prepare database records for the test
        df = pd.read_excel("candidates.xlsx")
        for index, row in df.iterrows():
            candidate_no = row['cand_no']
            first_name = row['first_name']
            last_name = row['last_name']
            phone_no = str(row['phone_no'])
            # if candidate's record is not found in database, create one
            if db.session.query(Candidates).filter_by(candidate_no=candidate_no).first() is None:
                # draw one set of questions for each candidate
                index_df_list = q.get_ques_list(first_group, mid_group, last_group, ques_per_cat_list)
                ques_num_list, correct_ans_list = q.get_ques_num_ans_list(index_df_list)
                today = date.today()
                # convert Python list to delimited string or it could not be stored into database
                index_df_str = ",".join(str(item) for item in index_df_list)
                ques_num_str = ",".join(item for item in ques_num_list)
                correct_ans_str = ",".join(item for item in correct_ans_list)
                ans_list = ['0'] * len(index_df_list)
                ans_str = ",".join(item for item in ans_list)
                # indicate that the candidate has not yet attempted the test
                candidate = Candidates(candidate_no=candidate_no, first_name=first_name, last_name=last_name,
                                      phone_no=phone_no, date=today, index_df_str=index_df_str, ques_num_str=ques_num_str,
                                      correct_ans_str=correct_ans_str, ans_str=ans_str, ques_no=1, test_completed=False)
                db.session.add(candidate)
                db.session.commit()

        # add host IP in case you want multiple candidates to sit for the test on local network
        # run(debug=True, host='192.168.1.69', port=5001)
        app.run(debug=True, port=5001)