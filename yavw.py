#!/usr/bin/env python3
# using (once again) http://blog.luisrei.com/articles/flaskrest.html
# Lab 4 server for 50.020 - vulnerable to XSS, SQLi, Command injection
# Nils, SUTD, 2017

from flask import Flask, render_template,request,redirect,make_response,session
import sqlite3
import os
import hashlib
import subprocess
db = "storage.db"

app = Flask(__name__)

def hash(data):
    """ Wrapper around sha224 """
    return hashlib.sha224(data.replace('\n','').encode('ascii')).hexdigest()

@app.route('/')
def main():
    if not 'username' in session:
        return redirect("/login",303)
    ul = None
    return render_template('main.html', name=session['username'][0], users=ul,news=getNews())

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('form.html')
    elif request.method == 'POST':
        conn = sqlite3.connect('storage.db')
        c=conn.cursor()
        email = request.form['email']        
        password = hash(request.form['password'])
        print("SELECT * FROM users WHERE email='%s' and password='%s'"%(email,password))
        c.execute("SELECT * FROM users WHERE email='%s' and password='%s'"%(email,password))
        rval=c.fetchone()
        if email == 'admin@a.com' and password == app.adminhash:
            rval=('admin','admin','admin')
        if rval:
            session['username'] = rval          
            return redirect("/",303)
        else:
            return render_template('form.html', error='Username or password incorrect!')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect("/login",303)    
        
@app.route('/search')
def search():
    if not 'username' in session:
        return redirect("/login",303)
    term = request.args.get('term')
    return render_template('main.html', name=session['username'][0],error="Search not implemented yet. Could not find "+term,news=getNews())

def getNews():
    conn = sqlite3.connect('storage.db')
    c=conn.cursor()
    return c.execute("SELECT * FROM news").fetchall()

@app.route('/news')
def news():
    if not 'username' in session:
        return redirect("/login",303)
    term = request.args.get('text')
    conn = sqlite3.connect('storage.db')
    c=conn.cursor()
    print(term)
    c.execute("insert into news (source,text) values (?,?)",(session['username'][0],term))
    conn.commit()
    return render_template('main.html', name=session['username'][0],news=getNews())


@app.route('/ping', methods=['POST'])
def ping():
    cmd = 'ping -c 1 '+ request.form['target']
    stream = os.popen(cmd)
    rval = stream.read()
    return render_template('main.html', name=session['username'][0], error3=rval, news=getNews())

if __name__ == '__main__':

    with open('secrets','r') as f:
        s = f.readlines()
    app.secret_key = s[0].replace('\n','')
    app.adminhash=hash(s[1])
    alicehash=hash(s[2])
    
    try:
        os.remove(db)
    except OSError:
        pass
    conn = sqlite3.connect(db)
    c=conn.cursor()
    c.execute("create table NEWS(source string, text string)")
    c.execute("create table USERS(name string, password string, email string)")
    c.execute("insert into users (email, name,password) values ('alice@alice.com','alice','"+alicehash+"')")
    conn.commit()
    app.config.update(SESSION_COOKIE_HTTPONLY=False)
    app.run(debug=True)
