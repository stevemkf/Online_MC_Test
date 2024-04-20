<ol>
<li>This app conducts online multiple choice (MC) test for candidates.<br/></li>
<li>candidates.xlsx - administrator enters candidates' information here then transferred to data.db through admin.html.  A candidate can attempt the test more than once.  Each attempt is identified by a 'batch no'.<br/></li>
<li>static/test_config - store test parameters of different trades, e.g. which question bank, how questions are to be drawn, etc. for the app.  The questions can be divided into different groups and categories by means of their numbers, e.g. M01A, N03B, etc.  How many questions drawn from each category and from which groups can be specified in the configuration file.<br/></li>
<li>static/questions - store the question banks of different trades.<br/></li>
<li>static/image - store the pictures used in questions.<br/></li>
<li>static/scores - store the test results for different trades and test batches.<br/></li>
<li>instance/data.db - the test database, holds the test information of all candidates, including the test questions assigned, the answers and scores.<br/></li>
<li>index.html - login page for candidates and administrator<br/></li>
<li>mc_test.html - each time this page is visited, a question and answer choices are presented to the candidate.  Apart from picking the answer, candidate can choose to move forward or backward, save answers in server, or end the test.<br/></li>
<li>admin.html - allow administrator to create new candidate records in SQLlite database (i.e. instance/data.db); change candidates' "test_completed" status; compute final scores and produce scores.xlsx.<br/></li>
<li>main.py - Make use of Flask library to interact with index.html, mc_test.html and admin.html.  Make use of session variables wherever needed.<br/></li>
<li>read_config.py - read the configuration file and create some global variables for the app<br/></li>
<li>draw_ques.py - consists of the DrawQuestion class and its functions to draw questions from the question bank.<br/></li>
<li>computer_scores.py - read the test database (i.e. data.db) and update the final_score column for those candidates who have completed the test.  The results can also be downloaded as Excel file.<br/></li>
</ol>
