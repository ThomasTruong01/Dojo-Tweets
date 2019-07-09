from flask import Flask, render_template, redirect, flash, request, session
from mysqlconnection import MySQLConnection
from validate_email import validate_email
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = 'shhdonttellanyone'
bcrypt = Bcrypt(app)


@app.route('/')
def main():
    if session.get('login'):
        if session['login']:
            return render_template('success.html')
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
        mySql = MySQLConnection('basic_regstration')
        query = 'SELECT count(email) as "UserCreated" FROM users WHERE email = %(em)s'
        data = {'em': request.form['email']}
        UserCreated = mySql.query_db(query, data)
        print(UserCreated)
        UserCreated = UserCreated[0]['UserCreated'] > 0
        print(UserCreated)
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
        mySql = MySQLConnection('basic_regstration')
        query = 'INSERT INTO users (first_name, last_name, email, password, created_on, updated_on) ' +\
            'VALUES (%(fn)s, %(ln)s, %(em)s, %(pw)s,now(),now())'
        pw = bcrypt.generate_password_hash(request.form['pw1'])

        data = {'fn': request.form['fName'], 'ln': request.form['lName'],
                'em': request.form['email'], 'pw': pw}
        mySql.query_db(query, data)
        flash('User created!')
    return redirect('/')


@app.route('/login', methods=['POST'])
def login():
    print(request.form)
    mySql = MySQLConnection('basic_regstration')
    query = 'SELECT * FROM users WHERE email = %(em)s'
    data = {'em': request.form['email']}
    pw = bcrypt.generate_password_hash(request.form['pw1'])
    pw_hash = mySql.query_db(query, data)
    print('*'*50)
    print('pw_hash', pw_hash[0]['password'])
    print('pw   ', pw)
    print('*'*50)
    session['fName'] = pw_hash[0]['first_name']
    session['lName'] = pw_hash[0]['last_name']
    session['email'] = pw_hash[0]['email']
    print(session)
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
            return render_template('dashboard.html')
    else:
        return redirect('/')


@app.route('/tweets/create', methods=['POST'])
def createTweet():


@app.route('/logout')
def logout():
    session['login'] = False
    session.clear()
    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True)
