<ol>
<li>This app conducts online MC tests for multiple candidates.<br/></li>
<li>candidates.xlsx - the administrator should enter candidates information here before the test begins (i.e. main.py is run).  A candidate can attempt the test more than once.  Each attempt is identified by a 'batch no'.<br/></li>
<li>config.xlsx - this file provides some flexibilities, e.g. filenames, how questions are to be drawn, etc. for the app.  The questions can be divided into different groups and categories by means of their numbers, e.g. M01A, N03B, etc.  How many questions drawn from each category and from which groups can be specified in this configuration file.<br/></li>
<li>read_config.py - read the configuration file and create some global varibles<br/></li>
<li>draw_ques.py - consists of the DrawQuestion class and functions to draw questions from the question bank (i.e. questions.xlsx).<br/></li>
<li>index.html - login page for candidates<br/></li>
<li>mc_test.html - each time this page is visit, a question and the answer choices are presented.  Apart from picking the answer, candidate can choose to move forward or backward, save the answers in server, or end the test.<br/></li>
<li>main.py - read candidates.xlsx to create new records in SQLlite database (i.e. instance/data.db).  Use Flask codes to interact with index.html and mc_test.html  Make use of session variables wherever needed.<br/></li>
<li>data.db - the test database, can have records from several test batches<br/></li>
<li>computer_scores.py - read the test database and update the final_score column for those candidates who have completed the test.  The results are also saved to an Excel file (i.e. scores.xlsx) for easy access.<br/></li>
<li>scores.xlsx - contains andidates' scores<br/></li>
<li>static/image - store the pictures used in questions.<br/></li>
</ol>
