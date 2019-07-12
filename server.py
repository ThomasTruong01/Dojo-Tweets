from flask import Flask, render_template, redirect, flash, request, session
from datetime import datetime
from mysqlconnection import MySQLConnection
from validate_email import validate_email
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = 'shhdonttellanyone'
bcrypt = Bcrypt(app)


@app.route('/')
def main():

    if 'login' in session:
        if session['login'] == True:
            return render_template('success.html')
        else:
            return render_template('index.html')
    else:
        return render_template('index.html')


@app.route('/process', methods=['POST'])
def process():
    session['fName'] = request.form['fName']
    session['lName'] = request.form['lName'],
    session['email'] = request.form['email']

    is_valid = True
    if len(request.form['fName']) < 1:
        flash("Please enter in your First Name")
    elif not request.form['fName'].isalpha():
        is_valid = False
        flash('First Name is not a valid entry')

    if len(request.form['lName']) < 1:
        flash("Please enter in your Last Name")
    elif not request.form['lName'].isalpha():
        is_valid = False
        flash('Last Name is not a valid entry')

    if not validate_email(request.form['email']):
        is_valid = False
        flash('Please enter in a valid email.')

    if is_valid:
        mySql = MySQLConnection('dojo_tweets')
        query = 'SELECT count(email) as "UserCreated" FROM users WHERE email = %(em)s'
        data = {'em': request.form['email']}
        UserCreated = mySql.query_db(query, data)
        UserCreated = UserCreated[0]['UserCreated'] > 0
    if UserCreated:
        is_valid = False
        flash('Email has been taken, please use a different email.')

    SpecialSym = ['$', '@', '#', '%']
    if len(request.form['pw1']) < 5:
        flash("Please enter a password with 5 or more characters")
        is_valid = False
    elif request.form['pw1'] != request.form['pw2']:
        flash('Your passwords does not match')
        is_valid = False
    elif len(request.form['pw1']) < 6:
        flash('length should be at least 6')
        is_valid = False
    elif len(request.form['pw1']) > 20:
        flash('length should be not be greater than 8')
        is_valid = False
    elif not any(char.isdigit() for char in request.form['pw1']):
        flash('Password should have at least one numeral')
        is_valid = False
    elif not any(char.isupper() for char in request.form['pw1']):
        flash('Password should have at least one uppercase letter')
        is_valid = False
    elif not any(char.islower() for char in request.form['pw1']):
        flash('Password should have at least one lowercase letter')
        is_valid = False
    elif not any(char in SpecialSym for char in request.form['pw1']):
        flash('Password should have at least one of the symbols $@#')
        is_valid = False

    if is_valid:
        mySql = MySQLConnection('dojo_tweets')
        query = 'INSERT INTO users (first_name, last_name, email, password, gender_id, birthday, created_on, updated_on) ' +\
            'VALUES (%(fn)s, %(ln)s, %(em)s, %(pw)s, %(gen)s, %(bday)s, now(),now())'
        pw = bcrypt.generate_password_hash(request.form['pw1'])

        data = {'fn': request.form['fName'], 'ln': request.form['lName'],
                'em': request.form['email'], 'pw': pw, 'gen': request.form['gender'],
                'bday': request.form['birthday']}
        mySql.query_db(query, data)
        flash('User created!')
    return redirect('/')


@app.route('/login', methods=['POST'])
def login():
    mySql = MySQLConnection('dojo_tweets')
    query = 'SELECT * FROM users WHERE email = %(em)s'
    data = {'em': request.form['email']}
    # pw = bcrypt.generate_password_hash(request.form['pw1'])
    pw_hash = mySql.query_db(query, data)
    session['userId'] = pw_hash[0]['id']
    session['fName'] = pw_hash[0]['first_name']
    session['lName'] = pw_hash[0]['last_name']
    session['email'] = pw_hash[0]['email']
    if bcrypt.check_password_hash(
            pw_hash[0]['password'], request.form['pw1']):
        session['login'] = True
        return redirect('/success')
    else:
        flash('Wrong Password')
        return redirect('/')


@app.route('/success')
def success():
    if session.get('login'):
        if session['login']:
            return redirect('/dashboard')
    else:
        return redirect('/')


@app.route('/dashboard')
def dashboard():
    mySql = MySQLConnection('dojo_tweets')
    query = 'SELECT users.id as "userId", first_name, last_name, tweets.id as "tweetId", tweets, tweets.created_on as "created_on", likes, liked FROM users LEFT JOIN tweets ON users.id = %(uid)s LEFT JOIN (select tweets_id, count(id) as "likes" from likes GROUP BY tweets_id) as mylikes ON tweets.id = mylikes.tweets_id LEFT JOIN (SELECT users_id as "uid", tweets_id, count(likes.id)>0 as "liked" FROM likes GROUP BY tweets_id, users_id) as liked ON liked.uid = tweets.users_id and liked.tweets_id = tweets.id ORDER BY tweets.id desc'
    data = {'uid': session['userId']}
    myFeed = mySql.query_db(query, data)
    # print(myFeed)

    return render_template('dashboard.html', myFeed=myFeed)


@app.route('/tweets/create', methods=['POST'])
def createTweet():
    session['tweet'] = request.form['tweet']
    is_valid = True
    if len(request.form['tweet'].strip()) < 1:
        is_valid = False
        flash('You forgot to write your tweet...')
        session.pop('tweet')

    if len(request.form['tweet'].strip()) > 255:
        is_valid = False
        flash('Your tweet is too long!')
        session['tweet'] = request.form['tweet']

    if is_valid:
        mySql = MySQLConnection('dojo_tweets')
        query = 'INSERT INTO tweets (tweets, users_id, created_on, updated_on) VALUES (%(tweets)s, %(id)s, now(), now())'
        data = {'tweets': request.form['tweet'].strip(
        ), 'id': session['userId']}
        mySql.query_db(query, data)
        session.pop('tweet')

    return redirect('/dashboard')


@app.route('/logout')
def logout():
    if 'login' in session:
        session.pop('login')
    session.clear()
    return redirect('/')


@app.route('/tweets/<tweetId>/add_like', methods=['POST'])
def like(tweetId):
    mySql = MySQLConnection('dojo_tweets')
    query = 'INSERT INTO likes (tweets_id, users_id, created_on, updated_on) ' +\
        'VALUES (%(tid)s, %(uId)s, now(), now())'
    data = {'tid': tweetId, 'uId': request.form['uId']}
    print(request.form)
    mySql.query_db(query, data)
    return redirect('/dashboard')


@app.route('/tweets/<tweetId>/delete_like', methods=['POST'])
def del_like(tweetId):
    mySql = MySQLConnection('dojo_tweets')
    query = 'DELETE FROM likes WHERE tweets_id = %(tid)s and users_id = %(uId)s'
    data = {'tid': tweetId, 'uId': request.form['uId']}
    print(request.form)
    mySql.query_db(query, data)
    return redirect('/dashboard')


@app.route('/tweets/<tweetId>/delete', methods=['POST'])
def delete_tweet(tweetId):
    mySql = MySQLConnection('dojo_tweets')
    query = 'DELETE FROM likes WHERE tweets_id = %(tid)s'
    data = {'tid': tweetId}
    mySql.query_db(query, data)
    mySql = MySQLConnection('dojo_tweets')
    query = 'DELETE FROM tweets WHERE id = %(tid)s'
    data = {'tid': tweetId}
    mySql.query_db(query, data)
    print("*"*50)
    print("*"*50)
    print('tweet deleted')
    print("*"*50)
    print("*"*50)
    return redirect('/dashboard')


@app.route('/tweets/<tweetId>/edit', methods=['POST'])
def edit_tweet(tweetId, methods=['POST']):
    mySql = MySQLConnection('dojo_tweets')
    query = 'Select * FROM tweets WHERE id = %(tid)s'
    data = {'tid': tweetId}
    myTweet = mySql.query_db(query, data)
    # print(myTweet)
    return render_template("edit.html", myTweet=myTweet[0])


@app.route('/tweets/<tweetId>/update', methods=['POST'])
def update_tweet(tweetId, methods=['POST']):
    mySql = MySQLConnection('dojo_tweets')
    query = 'UPDATE tweets Set tweets = %(tweet)s, updated_on = now() WHERE id = %(tid)s'
    data = {'tweet': request.form['tweet'], 'tid': tweetId}
    mySql.query_db(query, data)
    print("*"*50)
    print("*"*50)
    print(query)
    print("*"*50)
    print("*"*50)
    return redirect('/dashboard')


if __name__ == "__main__":
    app.run(debug=True)
