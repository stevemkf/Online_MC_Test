from datetime import datetime, date
import os
from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from markupsafe import Markup
from werkzeug.utils import secure_filename
from compute_scores import ComputeScores
from read_config import *

app = Flask(__name__)
app.config["SECRET_KEY"] = "there_is_no_secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
db = SQLAlchemy(app)
cs = ComputeScores(db)
create_trade_dicts()


# define the structure of database table
class Candidates(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trade = db.Column(db.String(10))
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
        trade = request.form["trade"].upper()
        session['trade'] = trade
        batch_no = int(request.form["batch_no"])
        session['batch_no'] = batch_no
        candidate_no = request.form["candidate_no"]
        password = request.form["password"]

        # administrator?
        if (candidate_no == "admin") and (password == "39076670"):
            session['administrator'] = "Steve Fung"
            return redirect("/admin")

        # check if the candidate's test data exist in database
        cand_data = db.session.query(Candidates).filter_by(trade=trade, batch_no=batch_no,
                                                           candidate_no=candidate_no).first()
        if cand_data is not None:
            # check password
            if password != cand_data.phone_no:
                flash("密碼不正確!", "error")
                flash("Password incorrect!", "error")
            # if the candidate has already completed the test (i.e. score >= 0),
            # he/she is not allowed to enter again
            elif cand_data.test_completed is True:
                flash("你的測驗已經結束!", "error")
                flash("You have already completed the test!", "error")
            else:
                # else, retrieve the data and keep them in session variables
                # this will avoid excessive access to database during the test
                session['id'] = cand_data.id
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
            flash("輸入資料不正確!", "error")
            flash("Input data incorrect!", "error")
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
    total_ques = len(session['ques_list'])
    if ques_no > total_ques:
        ques_no = 1
    if ques_no == 0:
        ques_no = total_ques
    session['ques_no'] = ques_no

    index_df = session['ques_list'][ques_no - 1]
    trade = session['trade']
    ques = ques_bank[trade].get_question(index_df)
    if ques["image"] == "":
        path_image = ""
    else:
        path_image = f"static/image/{trade}/{ques['image']}"
    # remember those answers which have already been entered by the candidate
    existing_ans = session['ans_list'][ques_no - 1]

    # show the question and answers to the candidate through HTML
    return render_template("mc_test.html",
                           ques_num=session['ques_no'],
                           question=ques["question"],
                           choice_1=ques["choice_1"],
                           choice_2=ques["choice_2"],
                           choice_3=ques["choice_3"],
                           choice_4=ques["choice_4"],
                           path_image=path_image,
                           existing_ans=existing_ans)


def update_ans(completed: bool):
    # save candidate's answers into database
    id = session['id']
    ans_list = session['ans_list']
    ans_str = ",".join(item for item in ans_list)

    candidate = db.session.query(Candidates).filter_by(id=id).first()
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
def init_test_batch(trade: str, batch_no: int):
    df = pd.read_excel("static/candidates.xlsx")
    filtered_dt = df.query('trade == @trade and batch_no == @batch_no')
    count = 0
    for index, row in filtered_dt.iterrows():
        candidate_no = row['cand_no']
        first_name = row['first_name']
        last_name = row['last_name']
        phone_no = str(row['phone_no'])
        # if candidate's record is not found in database, create one
        if db.session.query(Candidates).filter_by(trade=trade, batch_no=batch_no,
                                                  candidate_no=candidate_no).first() is None:
            # draw one set of questions for each candidate
            first_group = config[trade]['first group']
            if not isinstance(first_group, str):
                first_group = ""
            mid_group = config[trade]['mid group']
            last_group = config[trade]['last group']
            ques_per_cat_str = str(config[trade]['questions per category'])
            ques_per_cat_list = [int(item) for item in ques_per_cat_str.split(',')]
            index_df_list = ques_bank[trade].get_ques_list(first_group, mid_group, last_group, ques_per_cat_list)
            ques_num_list, correct_ans_list = ques_bank[trade].get_ques_num_ans_list(index_df_list)
            # convert Python list to delimited string or it could not be stored into database
            index_df_str = ",".join(str(item) for item in index_df_list)
            ques_num_str = ",".join(item for item in ques_num_list)
            correct_ans_str = ",".join(item for item in correct_ans_list)
            ans_list = ['0'] * len(index_df_list)
            ans_str = ",".join(item for item in ans_list)
            # indicate that the candidate has not yet attempted the test
            candidate = Candidates(trade=trade, batch_no=batch_no, candidate_no=candidate_no, first_name=first_name,
                                   last_name=last_name, phone_no=phone_no, index_df_str=index_df_str,
                                   ques_num_str=ques_num_str, correct_ans_str=correct_ans_str, ans_str=ans_str,
                                   ques_no=1, test_completed=False)
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

    trade = session['trade']
    batch_no = session['batch_no']                                    # for the first entry of this html page
    if request.method == "POST":
        trade = request.form["trade"].upper()
        batch_no = int(request.form["batch_no"])
        session['trade'] = trade
        session['batch_no'] = batch_no
        if "upload" in request.form:
            return redirect("/upload")
        if "init" in request.form:
            count = init_test_batch(trade, batch_no)
            flash(f"{count} records were newly added in the server.", "success")
        elif "show" in request.form:
            pass
        elif "terminate" in request.form:
            for candidate in db.session.query(Candidates).filter_by(trade=trade, batch_no=batch_no).all():
                candidate.test_completed = True
            db.session.commit()
            flash("Done.", "success")
        elif "compute" in request.form:
            path_scores = f"static/scores/{trade}_{batch_no}_scores.xlsx"
            cs.compute_scores(trade, batch_no, path_scores)
            message = Markup(f"<a href = {path_scores} download>Click here to download the scores.</a>")
            flash(message, category="success")
        elif "change" in request.form:
            candidate_no = request.form["candidate_no"]
            candidate = db.session.query(Candidates).filter_by(trade=trade, batch_no=batch_no,
                                                               candidate_no=candidate_no).first()
            if candidate is not None:
                status = candidate.test_completed
                candidate.test_completed = 1 - status
                db.session.commit()
                flash(f"Status was changed.", "success")
            else:
                flash("Candidate not found.  Please check.", "success")
    # data will be a list of tuples
    data = (db.session.query(Candidates.candidate_no, Candidates.last_name, Candidates.first_name, Candidates.ans_str,
                             Candidates.test_completed, Candidates.final_score).filter_by(trade=trade,batch_no=batch_no).all())
    # tuple contents cannot be modified
    # so data (a list of tuples) are converted to data1 (a list of lists)
    data1 = []
    for cand_tuple in data:
        cand_list = list(cand_tuple)
        # count how many questions that a candidate has answered
        ans_str = cand_list[3]
        ans_list = [item for item in ans_str.split(',')]
        ques_answered = sum(ans != "0" for ans in ans_list)
        cand_list[3] = str(ques_answered)
        data1.append(cand_list)
    heading = ("Candidate No.", "Last Name", "First Name", "No. of questions answered", "Test Completed", "Score")
    return render_template("admin.html", trade=trade, batch_no=batch_no, headings=heading, data=data1)


@app.route('/upload', methods=['GET'])
def upload():
    # if administrator has not logged in, direct to the log-in page
    if not 'administrator' in session.keys():
        return redirect("/")
    if session['administrator'] != "Steve Fung":
        return redirect("/")
    else:
        return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload_files():
    file_type = request.form["file_type"]
    trade = request.form["trade"].upper()
    uploaded_file = request.files["file"]
    filename = secure_filename(uploaded_file.filename)
    if filename != '':
        folder = "static"
        match file_type:
            case "candidates":
                if filename != "candidates.xlsx":
                    return "Invalid filename", 400
            case "questions":
                if filename != f"questions_{trade}.xlsx":
                    return "Invalid filename", 400
                else:
                    folder = "static/questions"
            case "image":
                file_ext = os.path.splitext(filename)[1]
                if file_ext not in [".bmp", ".jpg", ".png", ".gif"]:
                    return "Invalid file type", 400
                else:
                    folder = f"static/image/{trade}"
            case "test_config":
                if filename != f"config_{trade}.xlsx":
                    return "Invalid filename", 400
                else:
                    folder = "static/test_config"
        if not os.path.exists(folder):
            os.makedirs(folder)
        uploaded_file.save(os.path.join(folder, filename))
    # the client does not need to navigate away from its current page
    return '', 204


if __name__ == "__main__":
    with app.app_context():
        # the database should have already been created prior to uploading to the hosting server
        db.create_all()
        # add host IP in case you want multiple candidates to sit for the test on local network
        # app.run(debug=True, host='192.168.1.69', port=5001)
        app.run(debug=True, port=5001)