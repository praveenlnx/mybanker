# Imports section
from flask import Flask, render_template, request, session, flash, url_for, redirect
from functools import wraps
import fileinput, gc
from datetime import date
from reportHelper import inexTrend, expenseStats, inexTrendAll, categoryStats
from dbHelper import (
         runQueriesFromFile, checkLogin, getNameofUser, addUser, 
         updatePassword, listMybankerUsers, getCategories, addCategory, 
         checkTotalAccounts, addAccountDB, getAccounts, getTransactions,
         getCategoryType, addTransactionsDB, getNetworth, getInbox,
         getInboxCount, deleteMessageDB, sendMessage, markMsgRead,
         searchTransactions, getTransactionsForCategory
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
  networth = 0.00
  inexAllGraph = None
  unread = None
  if not request.method == "POST":
    if 'logged_in' in session:
      if session['username'] == 'admin':
        return render_template(dashboard_admin)
      jumbomessage = dashboardMessage(session['username'])
      if checkTotalAccounts(session['username']) != 0:
        accounts = getAccounts(session['username'])
        networth = getNetworth(session['username'])
        inexAllGraph = inexTrendAll(session['username'])
      unreadCount = getInboxCount(session['username'], "unread")
      if unreadCount > 0:
        unread = unreadCount
      return render_template(dashboard, jumbomessage=jumbomessage, accounts=accounts, networth=networth, inexAllGraph=inexAllGraph, unread=unread)
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
        networth = getNetworth(username)
        inexAllGraph = inexTrendAll(session['username'])
      unreadCount = getInboxCount(session['username'], "unread")
      if unreadCount > 0:
        unread = unreadCount
      return render_template(dashboard, jumbomessage=jumbomessage, accounts=accounts, networth=networth, inexAllGraph=inexAllGraph, unread=unread)
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
@app.route('/<username>/account/<accountname>/<period>', methods=['GET', 'POST'])
@login_required
def account_transactions(username, accountname, period):
  transactions = year = month = None
  if username and accountname and period:
    if request.method == "POST":
      year = request.form['year']
      month = request.form['month']
    transactions = getTransactions(username, accountname, period, year, month)
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

# Search Route
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
  searchresults = listresults = None
  if request.method == "POST":
    if request.form['searchForm'] == "search":
      keyword = request.form['keyword']
      searchresults = searchTransactions(session['username'], keyword)
    else:
      category = request.form['listcategory']
      period = request.form['period']
      year = request.form['year']
      month = request.form['month']
      if category == "Select":
        flash("Please choose a category")
      else:
        if not "Select" in period:
          listresults = getTransactionsForCategory(session['username'], category, period, None, None)
        elif not "Select" in year and not "Select" in month:
          listresults = getTransactionsForCategory(session['username'], category, None, year, month)
        else:
          flash("Please choose period carefully. If you didn't select one of the predefined period, you have to select both year and month")
        if listresults is None:
          flash("No transacations to list")
  categories = getCategories()
  return render_template('searchtransactions.html', searchresults=searchresults, listresults=listresults, categories=categories)


# Reports Route
@app.route('/reports', methods=['GET', 'POST'])
@login_required
def reports():
  if checkTotalAccounts(session['username']) == 0:
    flash("No reports as you don't have any accounts setup. Please start adding your accounts")
    jumbomessage = dashboardMessage(session['username'])
    return render_template('dashboard.html', jumbomessage=jumbomessage)
  inexYear = expenseYear = date.today().year
  categoryStatsGraph = None
  categoryStatsData = None
  if request.method == "POST":
    if 'inexyear' in request.form:
      inexYear = request.form['inexyear']
    elif 'expyear' in request.form:
      expenseYear = request.form['expyear']
    elif 'statcategory' in request.form:
      statcategory = request.form['statcategory']
      categoryStatsGraph, categoryStatsData = categoryStats(session['username'], statcategory)
  categories = getCategories()
  inexGraph = inexTrend(session['username'], inexYear)
  expenseGraph = expenseStats(session['username'], expenseYear)
  return render_template('reports.html', inexGraph=inexGraph, expenseGraph=expenseGraph, categories=categories, categoryStatsGraph=categoryStatsGraph, categoryStatsData=categoryStatsData)

# Messages Route
@app.route('/messages', methods=['GET', 'POST'])
@login_required
def messages():
  mails = getInbox(session['username'])
  unread = getInboxCount(session['username'], "unread")
  tousers = listMybankerUsers()
  users = [name for name in tousers if name[1] != session['username']]
  return render_template('messages.html', mails=mails, unread=unread, users=users)

# Delete message Route
@app.route('/deletemessage/<msgid>')
@login_required
def deletemessage(msgid):
  if deleteMessageDB(msgid):
    flash("Message deleted")
  else:
    flash("Delete operation failed")
  return redirect(url_for('messages'))

# Send message Route
@app.route('/sendmessage', methods=['GET', 'POST'])
@login_required
def sendmessage():
  if request.method == "POST":
    subject = request.form['subject']
    message = request.form['message']
    touser = request.form['touser']
    flash(sendMessage(session['username'], subject, message, touser))
    return redirect(url_for('messages'))
  else:
    return redirect(url_for('messages'))

# View Message Route
@app.route('/viewmessage/<msgid>')
@login_required
def viewmessage(msgid):
  mail = getInbox(session['username'], msgid)
  markMsgRead(msgid)
  return render_template('viewmessage.html', mail=mail)

# Main Function
if __name__ == "__main__":
  app.run(port=8002, debug=True)
