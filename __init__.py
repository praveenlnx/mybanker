# Imports section
from flask import Flask, render_template, request, session, flash
from functools import wraps
import fileinput, gc
from dbHelper import (
         runQueriesFromFile, checkLogin, getNameofUser, addUser, 
         updatePassword, listMybankerUsers, getCategories, addCategory, 
         checkTotalAccounts, addAccountDB, getAccounts, getTransactions,
         getCategoryType, addTransactionsDB
         )

# Initialize Flask object
app = Flask(__name__)
app.secret_key = 'i234aessser54234lajdflkjasdlkjf;oiuqaewrlrl'

# Load configuration from file
app.config.from_object('config')

# Login_required decorator
def login_required(f):
  @wraps(f)
  def decorated_function(*args, **kwargs):
    if 'logged_in' in session:
      return f(*args, **kwargs)
    else:
      return render_template('index.html', message=None)
  return decorated_function

# Index Route 
@app.route('/')
def index():
  if app.config['INITIAL_SETUP'].lower() != 'done':
    return render_template('install_welcome.html')
  else:
    return render_template('index.html', message=None)

# Login Dashboard Route
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
  dashboard = 'dashboard.html'
  dashboard_admin = 'dashboard_admin.html'
  jumbomessage = None
  accounts = None
  if not request.method == "POST":
    if 'logged_in' in session:
      if session['username'] == 'admin':
        return render_template(dashboard_admin)
      jumbomessage = dashboardMessage(session['username'])
      if checkTotalAccounts(session['username']) != 0:
        accounts = getAccounts(session['username'])
      return render_template(dashboard, jumbomessage=jumbomessage, accounts=accounts)
    return render_template('index.html', message="You need to login first", mtype="warning")
  username = request.form['username']
  password = request.form['password']
  if checkLogin(username, password):
    session['logged_in'] = True
    session['username'] = username
    session['user'] = getNameofUser(username)
    if username == "admin":
      return render_template(dashboard_admin)
    else:
      jumbomessage = dashboardMessage(username)
      if checkTotalAccounts(username) != 0:
        accounts = getAccounts(username)
      return render_template(dashboard, jumbomessage=jumbomessage, accounts=accounts)
  else:
    return render_template('index.html', message="Invalide credentials. Please try again", mtype="danger")

def dashboardMessage(username):
  jumbomessage = []
  # Check how many accounts the user has got
  accounts = checkTotalAccounts(username)
  if accounts == 0:
    jumbomessage.append("You don't have any accounts setup. Please add a new account to manage and start tracking.")
  else:
    jumbomessage.append("You have %s accounts configured." % accounts)
  return jumbomessage

# Setup MyBanker Route
@app.route('/setup', methods=['GET', 'POST'])
def setup():
  # Check if the application is already configured
  if app.config['INITIAL_SETUP'] == 'done':
    return render_template('setupdone.html')

  queryResult = runQueriesFromFile("templates/mybanker-initial.sql")
  if not "Success" in queryResult:
    flash("Error while trying to populate database : %s" % queryResult)
    return render_template('install_welcome.html')

  app.config['INITIAL_SETUP'] = 'done'
  
  # Update config file to mark initial setup as complete
  for line in fileinput.input("config.py", inplace=True):
    print(line.replace("pending", "done")),

  return render_template('install_complete.html')

# Logout Route
@app.route('/logout')
@login_required
def logout():
  session.clear()
  return render_template('index.html', message="You have been logged out!", mtype="info")

# Add User route
@app.route('/adduser', methods=['GET', 'POST'])
@login_required
def adduser():
  if request.method == "POST":
    name = request.form['name']
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    data = addUser(name, username, password, email)
    flash(data)
  return render_template('adduser.html')

# Change Admin Password route
@app.route('/changeAdminPass', methods=['GET', 'POST'])
@login_required
def changeAdminPass():
  if request.method == "POST":
    currentPW = request.form['currentpw']
    newPW = request.form['newpw']
    data = updatePassword('admin', currentPW, newPW)
    flash(data)
  return render_template('change_admin_pass.html')

# List User Route
@app.route('/listuser')
@login_required
def listuser():
  userdict = listMybankerUsers()
  return render_template('listuser.html', userdict=userdict)

# Manage categories Route
@app.route('/managecategories', methods=['GET', 'POST'])
@login_required
def managecategories():
  if request.method == "POST":
    if 'incategory' in request.form:
      data = addCategory(request.form['incategory'], 'IN')
    else:
      data = addCategory(request.form['excategory'], 'EX')
    flash(data)
  inc_categories, exp_categories = getCategories()
  return render_template('managecategories.html', inc_categories=inc_categories, exp_categories=exp_categories)

# Add Account Route
@app.route('/addaccount', methods=['GET', 'POST'])
@login_required
def addaccount():
  if request.method == "POST":
    accinfo = {}
    accinfo['name'] = request.form['accountname']
    accinfo['owner'] = session['username']
    accinfo['balance'] = request.form['accountbalance']
    accinfo['notes'] = request.form['accountnotes']
    accinfo['exclude'] = 'no'
    if 'exclude' in request.form:
      accinfo['exclude'] = 'yes'
    accinfo['type'] = 'A'
    if request.form['accounttype'] == 'liability':
      accinfo['type'] = 'L'
    flash(addAccountDB(accinfo))
  return render_template('addaccount.html')

# Account Transactions Route
@app.route('/<username>/account/<accountname>')
@login_required
def account_transactions(username, accountname):
  transactions = None
  if username and accountname:
    transactions = getTransactions(username, accountname)
    accinfo = getAccounts(username, accountname)
  return render_template('account-transactions.html', username=username, accinfo=accinfo, transactions=transactions)

# Add a new transaction Route
@app.route('/addtransaction', methods=['GET', 'POST'])
@login_required
def addtransaction():
  inc_categories, exp_categories = getCategories()
  categories = exp_categories + inc_categories
  accounts = getAccounts(session['username'])
  if request.method == "POST":
    account = request.form['account']
    category = request.form['category']
    amount = request.form['amount']
    date = request.form['date']
    notes = request.form['notes']
    flash(addTransactionsDB(date, notes, amount, category, account, session['username']))
  return render_template('addtransaction.html', categories=categories, accounts=accounts)

# Transfer funds Route
@app.route('/transferfunds', methods=['GET', 'POST'])
@login_required
def transferfunds():
  accounts = getAccounts(session['username'])
  if request.method == "POST":
    fromacc = request.form['fromaccount']
    toacc = request.form['toaccount']
    amount = request.form['amount']
    date = request.form['date']
    notes = request.form['notes']
    addTransactionsDB(date, notes, amount, "TRANSFER OUT", fromacc, session['username'])
    addTransactionsDB(date, notes, amount, "TRANSFER IN", toacc, session['username'])
    flash("Funds transferred from %s to %s successfully" % (fromacc, toacc))
  return render_template('transferfunds.html', accounts=accounts)

# Main Function
if __name__ == "__main__":
  app.run(port=8002, debug=True)
