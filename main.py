from flask import Flask, render_template, request, redirect, session
from draw_ques import DrawQuestions
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date


app = Flask(__name__)
app.config["SECRET_KEY"] = "there_is_no_secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
db = SQLAlchemy(app)                        # Candidates' data will be saved onto database
q = DrawQuestions()                         # Carry out the preparation.  Questions will be drawn later.


# define the structure of database table
class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    candidate_no = db.Column(db.String(20))
    first_name = db.Column(db.String(40))
    last_name = db.Column(db.String(20))
    date = db.Column(db.Date)
    time = db.Column(db.Time)
    ques_num_list = db.Column(db.String(1000))
    correct_ans_list = db.Column(db.String(400))
    ans_list = db.Column(db.String(400))
    final_score = db.Column(db.Integer)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        session['candidate_no'] = request.form["candidate_no"]
        ques_list = q.get_ques_list()                           # draw one set of questions for each candidate
        session['ques_list'] = ques_list
        session['ques_num_list'], session['correct_ans_list'] = q.get_ques_num_ans_list(ques_list)
        session['total_ques'] = len(session['ques_list'])
        session['ans_list'] = ['0'] * session['total_ques']     # each candidate has his/her answer list as well
        session['ques_no'] = 1

        today = date.today()
        t_now = datetime.now().time()

        # convert Python list to delimited string or it could not be stored into database
        ques_num_list = ",".join(item for item in session['ques_num_list'])
        correct_ans_list = ",".join(item for item in session['correct_ans_list'])
        candidate = Candidate(candidate_no=session['candidate_no'], date=today, time=t_now, ques_num_list=ques_num_list,
                              correct_ans_list=correct_ans_list)
        db.session.add(candidate)
        db.session.commit()

        session.modified = True
        return redirect("/test")

    return render_template("index.html")


@app.route("/test", methods=["GET", "POST"])
def test():

    # candidate must log in first
    if not 'candidate_no' in session.keys():
        return redirect("/index")


    increment = 0  # Python interpreter insists declare the variable first
    if request.method == "POST":
        # save the candidate's chosen answer
        if "answer" in request.form:
            answer = request.form["answer"]
            session['ans_list'][session['ques_no'] - 1] = answer

        # end of the test?
        if "finish" in request.form:
            # without the following line, the answer picked just before finish would not be passed by session variable
            session.modified = True
            return redirect("/finish")

        # the candidate wants to move the next or previous question?
        if "direction" in request.form:
            direction = request.form["direction"]
            if direction == "next":
                increment = 1
            elif direction == "prev":
                increment = -1


    ques_no = session['ques_no'] + increment
    if ques_no > session['total_ques']:
        ques_no = 1
    if ques_no == 0:
        ques_no = session['total_ques']
    session['ques_no'] = ques_no

    # prepare the next/previous question
    index_df = session['ques_list'][ques_no - 1]
    ques = q.get_question(index_df)
    exist_ans = session['ans_list'][ques_no - 1]

    # show the question and answers to the candidate through HTML
    return render_template("test.html",
                           ques_num=session['ques_no'],
                           question=ques["question"],
                           choice_1=ques["choice_1"],
                           choice_2=ques["choice_2"],
                           choice_3=ques["choice_3"],
                           choice_4=ques["choice_4"],
                           fname_image=ques["image"],
                           exist_ans=exist_ans)


@app.route("/finish")
def finish():
    # candidate's answers will be stored in database
    candidate_no = session["candidate_no"]
    ans_list = session['ans_list']
    ans_list_str = ",".join(item for item in ans_list)
    print(ans_list)

    # compare candidate's answers to the correct answers, hence calculate the final score
    candidate = Candidate.query.filter_by(candidate_no=candidate_no).first()
    correct_ans_list = candidate.correct_ans_list.split(",")
    final_score = 0
    for index in range(0, session['total_ques']):
        if ans_list[index] == correct_ans_list[index]:
            final_score = final_score + 1

    # save candidate's answers and final score to database
    candidate.ans_list = ans_list_str
    candidate.final_score = final_score
    db.session.commit()

    # clear the Session variables
    session.clear()
    return "<p>Test finished!</p>"


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        app.run(debug=True, host='192.168.1.69', port=5003)
