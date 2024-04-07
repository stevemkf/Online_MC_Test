from flask import Flask, render_template, request, redirect, session
from flask_session import Session
from draw_ques import DrawQuestions

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
q = DrawQuestions()
ans_list = ['0'] * q.total_ques_paper


@app.route("/", methods=["GET", "POST"])
def index():
    increment = 0                               # Python interpreter insisted adding this line

    if request.method == "POST":
        direction = request.form["direction"]
        if direction == "next":
            increment = 1
        elif direction == "prev":
            increment = -1

        if "answer" in request.form:
            answer = request.form["answer"]
            ans_list[session['ques_no'] - 1] = answer

    if not session.get("ques_no"):
        session['ques_no'] = 1
    else:
        session['ques_no'] = session['ques_no'] + increment

    if session['ques_no'] > q.total_ques_paper:
        session['ques_no'] = 1
    if session['ques_no'] == 0:
        session['ques_no'] = q.total_ques_paper

    d = q.get_question(session['ques_no'] - 1)

    return render_template("index.html",
                           ques_num=session['ques_no'],
                           question=d["question"],
                           choice_1=d["choice_1"],
                           choice_2=d["choice_2"],
                           choice_3=d["choice_3"],
                           choice_4=d["choice_4"],
                           fname_image=d["image"])

@app.route("/logout")
def logout():
    session["ques_no"] = None
    return redirect("/")


if __name__ == "__main__":
    with app.app_context():
        app.run(debug=True, port=5001)
