from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import gettempdir
from helpers import *

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///roster.db")

@app.route("/")
@login_required
def index():
    
    # query database for user's submitted blocks and requests
    user = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])
    requests = db.execute("SELECT date, comment FROM requests WHERE userid = :userid AND date >= DATE('now','start of month','+1 month') ORDER BY date", userid=session["user_id"])
    blocks = db.execute("SELECT date, comment FROM blocks WHERE userid = :userid AND date >= DATE('now','start of month','+1 month') ORDER BY date", userid=session["user_id"])

    # generate dashboard with user's information
    return render_template("index.html", requests=requests, blocks=blocks, points=user[0]['points'], username=user[0]['username'])

@app.route("/rmblock", methods=["POST"])
@login_required
def rmblock():
    
    # delete selected call block
    if request.method == "POST":
        db.execute("DELETE FROM blocks WHERE date = :date AND userid = :id", id=session["user_id"], date=request.form['date'])
        
        # return to index page and flash message
        flash('Call block removed!')
        return redirect(url_for("index"))

@app.route("/rmrequest", methods=["POST"])
@login_required
def rmrequest():
    
    # delete selected call request
    if request.method == "POST":
        db.execute("DELETE FROM requests WHERE date = :date AND userid = :id", id=session["user_id"], date=request.form['date'])
        
        # return to index page and flash message
        flash('Call request removed!')
        return redirect(url_for("index"))

@app.route("/blocks", methods=["GET", "POST"])
@login_required
def blocks():
    """View and submit call blocks."""
    
    # check validity of inputs on form
    if request.method == "POST":
        if request.form["date"] == "" or request.form["comment"] == "":
            flash('Must provide date and reason!')
            return redirect(url_for("blocks"))
        
        # proceed to record block
        db.execute("INSERT INTO blocks (userid, date, comment) VALUES(:userid, :date, :comment)", userid=session["user_id"], date=request.form["date"], comment=request.form["comment"])
        
        # flash message and update page
        flash('Call block submitted!')
        return redirect(url_for("blocks"))
    
    else:
        # query database for next month's blocks
        blocks = db.execute("SELECT date, comment, timestamp, username FROM blocks JOIN users ON blocks.userid = users.id WHERE date >= DATE('now','start of month','+1 month') ORDER BY date")
        
        # display all blocks
        return render_template("blocks.html", blocks=blocks)

@app.route("/requests", methods=["GET", "POST"])
@login_required
def requests():
    """View and submit call requests."""
    
    # check validity of inputs on form
    if request.method == "POST":
        if request.form["date"] == "" or request.form["comment"] == "":
            flash('Must provide date and reason!')
            return redirect(url_for("requests"))
        
        # proceed to record request
        db.execute("INSERT INTO requests (userid, date, comment) VALUES(:userid, :date, :comment)", userid=session["user_id"], date=request.form["date"], comment=request.form["comment"])
        
        # flash message and update page
        flash('Call request submitted!')
        return redirect(url_for("requests"))
    
    else:
        # query database for next month's requests
        requests = db.execute("SELECT date, comment, timestamp, username FROM requests JOIN users ON requests.userid = users.id WHERE date >= DATE('now','start of month','+1 month') ORDER BY date")
        
        # display all requests
        return render_template("requests.html", requests=requests)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # if user reached route via POST (as by submitting a form)
    if request.method == "POST":
        # check validity of inputs on form
        if request.form["username"] == "" or request.form["password"] == "":
            flash('Must provide username and password!')
            return redirect(url_for("login"))

        # query database for username
        user = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(user) != 1 or not pwd_context.verify(request.form.get("password"), user[0]["hash"]):
            flash('Invalid username and/or password!')
            return redirect(url_for("login"))

        # forget any user_id
        session.clear()
        
        # remember which user has logged in
        session["user_id"] = user[0]["id"]

        # redirect user to index page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login page
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    
    # check validity of inputs on form
    if request.method == "POST":
        if request.form["username"] == "" or request.form["password"] == "":
            flash('Must provide username and password!')
            return redirect(url_for("register"))
            
        if request.form["password"] != request.form["password2"]:
            flash('Passwords do not match!')
            return redirect(url_for("register"))
            
        # check username is available    
        user = db.execute("SELECT * FROM users WHERE username = :username", username=request.form["username"])
        if len(user) == 1:
            flash('Username not available!')
            return redirect(url_for("register"))
        
        # proceed to hash the password and add user into database
        hash = pwd_context.encrypt(request.form["password"])
        db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)", username=request.form["username"], hash=hash)
        
        # automatically login after registration success
        user = db.execute("SELECT * FROM users WHERE username = :username", username=request.form["username"])
        session["user_id"] = user[0]["id"]
        
        # redirect to index page and flash message
        flash('Successfully registered!')
        return redirect(url_for("index"))
    
    # display generic register page if reached via link
    else:
        return render_template("register.html")
        
@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """Allow user to change password."""
    
    # check validity of inputs on form
    if request.method == "POST":
        if request.form["oldpassword"] == "" or request.form["newpassword"] == "":
            flash('Must provide old and new password!')
            return redirect(url_for("settings"))

        if request.form["newpassword"] != request.form["newpassword2"]:
            flash('New passwords do not match!')
            return redirect(url_for("settings"))

        if request.form["oldpassword"] == request.form["newpassword"]:
            flash('Old and new passwords are identical!')
            return redirect(url_for("settings"))
            
        # check current password is correct
        user = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])
        if not pwd_context.verify(request.form.get("oldpassword"), user[0]["hash"]):
            flash('Invalid current password!')
            return redirect(url_for("settings"))
        
        # proceed to hash new password and update hash in database
        newhash = pwd_context.encrypt(request.form["newpassword"])
        db.execute("UPDATE users set hash = :hash WHERE id = :id", id=session["user_id"], hash=newhash)
        
        # return to index page and flash message 
        flash('Password successfully changed!')
        return redirect(url_for("index"))
    
    # display generic settings page if reached via link
    else:
        return render_template("settings.html")
        
@app.route("/duties", methods=["GET", "POST"])
@login_required
def duties():
    """Generate next month's duty roster and display points tally."""
    
    # query database for users and points
    users = db.execute("SELECT username, points FROM users ORDER BY id ASC")
    
    # get number of users
    num_users = len(users)
    
    # get current datetime
    import datetime
    now = datetime.datetime.now()
    
    # get first day of next month
    dt1 = now.replace(day=1)
    dt2 = dt1 + datetime.timedelta(days=32)
    next = dt2.replace(day=1)
    
    # get number of days in next month
    import calendar
    num_days_next_month = calendar.monthrange(next.year, next.month)[1]
    
    # create array to store assigned user_ids
    import numpy as np
    assigned = np.zeros(num_days_next_month, dtype=np.int)
    
    # create array to store users' current points
    points = np.zeros(num_users, dtype=np.int)
    for i in range(num_users):
        points[i] = users[i]['points']
        
    # create arrays to store number of weekdays/weekends assigned to each user
    weekdays = np.zeros(num_users, dtype=np.int)
    weekends = np.zeros(num_users, dtype=np.int)
    
    # first loop through every day next month
    for i in range(num_days_next_month):
        
        # retrieve any call requests for that day
        day_requests = db.execute("SELECT userid FROM requests WHERE date = DATE('now','start of month','+1 month', '+:i days') ORDER BY timestamp", i=i)
        
        # if call requests exist
        if len(day_requests) != 0:
            date = next + datetime.timedelta(days=i)
            
            # assign requestor on first-come-first-served basis
            oncall = day_requests[0]['userid']
            assigned[i] = oncall
            
            # if day is weekend, give 2 points and update weekend tracker
            if date.isoweekday() > 5:
                points[oncall-1] += 2
                weekends[oncall-1] +=1
            
            # else if day is weekday, give 1 point and update weekday tracker
            else:
                points[oncall-1] += 1
                weekdays[oncall-1] +=1
    
    # second loop through every day next month
    import random
    for i in range(num_days_next_month):
        
        # if no one has been assigned yet
        if assigned[i] == 0:    
            
            # create list of potential candidates to assign
            candidates = list(range(1, num_users+1))
            
            # retrieve any call blocks for that day
            day_blocks = db.execute("SELECT userid FROM blocks WHERE date = DATE('now','start of month','+1 month', '+:i days')", i=i)
            
            # drop all blockers from candidate list
            for j in range(len(day_blocks)):
                candidates.remove(day_blocks[j]['userid'])
            
            # drop all users oncall 3 days before and after that day (mandatory 3-day rest between calls)
            if i > 0 and assigned[i-1] in candidates:
                candidates.remove(assigned[i-1])
            if i > 1 and assigned[i-2] in candidates:
                candidates.remove(assigned[i-2])
            if i > 2 and assigned[i-3] in candidates:
                candidates.remove(assigned[i-3])
            if i < num_days_next_month-1 and assigned[i+1] in candidates:
                candidates.remove(assigned[i+1])
            if i < num_days_next_month-2 and assigned[i+2] in candidates:
                candidates.remove(assigned[i+2])
            if i < num_days_next_month-3 and assigned[i+3] in candidates:
                candidates.remove(assigned[i+3])
            
            # if day is weekend, assign candidate with least points 
            date = next + datetime.timedelta(days=i) 
            if date.isoweekday() > 5:
                for index, candidate in enumerate(candidates):
                    rank = points[candidate-1]
                oncall = candidates[np.argmin(rank)]
                assigned[i] = oncall
                
                # give 2 points and update weekend tracker
                points[oncall-1] += 2
                weekends[oncall-1] +=1
            
            # else if day is weekday, randomly assign any candidate
            else:
                oncall = random.choice(candidates)
                assigned[i] = oncall
                
                # give 1 point and update weekday tracker
                points[oncall-1] += 1
                weekdays[oncall-1] +=1
    
    # convert assigned from user_ids to names and generate corresponding arrays of days and dates
    names, dates, days = [], [], []
    for i, oncall in enumerate(assigned):
        names.append(users[oncall-1]['username'])
        date = next + datetime.timedelta(days=i)
        dates.append(date.date())
        days.append(date.strftime('%A'))
        
    # calculate group mean points
    average = np.mean(points)
    
    #if request.method == "POST":
    #    for i in range(num_users):
    #        db.execute("UPDATE users SET points = :points WHERE id = :id", id=users[i]['id'], points=points[i])

        # redirect to index page and flash message
    #    flash('Roster locked and points updated!')
    #    return redirect(url_for("index"))
        
    #else:
    # generate page with next month's roster and points summary
    return render_template("duties.html", users=users, ndnm=num_days_next_month, names=names, dates=dates, days=days, weekdays=weekdays, weekends=weekends, points=points, num_users=num_users, average=average)