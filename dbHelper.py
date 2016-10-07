# Import Section
from flask import Flask
from flask import current_app as app
from flaskext.mysql import MySQL
from hashlib import sha256
from operator import itemgetter
import calendar
import gc

app = Flask(__name__)
app.config.from_object('config')

mysql = MySQL()
mysql.init_app(app)

# Method to load and run all queries from a file
# Run queries one by one and return on first failure
def runQueriesFromFile(queryfile):

  conn = mysql.connect()
  cursor = conn.cursor()

  # Read all queries first
  with open (queryfile, "r") as myFile:
    loadQuery = myFile.readlines()

  # Run query one by one and return on first failure
  for query in loadQuery:
    if query:
      try:
        cursor.execute(query)
        conn.commit()
      except Exception as e:
        return str(e)
  conn.close()
  gc.collect() 
  return "Success"

# Method to validate login credentials entered
def checkLogin(username, password):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    cursor.execute('SELECT password FROM users WHERE username = "%s"' % username)
    for row in cursor.fetchall():
      if sha256(password).hexdigest() == row[0]:
        return True
      else:
        return False
  except Exception as e:
    conn.close()
    gc.collect()
    return False
  conn.close()
  gc.collect()

# Get Name from Username
def getNameofUser(username):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    cursor.execute('SELECT name FROM users WHERE username = "%s"' % username)
    return cursor.fetchone()[0]
  except Exception as e:
    conn.close()
    gc.collect()
    return False
  conn.close()
  gc.collect()

# Method to add new user
def addUser(name, username, password, email):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    query = "INSERT INTO users VALUES('%s', '%s', '%s', '%s', '%s', CURDATE())" % (name, username, 'no', sha256(password).hexdigest(), email)
    cursor.execute(query)
    conn.commit()
    # Send a welcome email to the new user
    mailSubject = "Welcome to MyBanker!"
    mailMsg = """
              Hi %s,
  
              Welcome to MyBanker, the Personal Finance Tracker.
              Please add new accounts and start tracking your incomes and expenses.

              Note:
              If you would like a new category that is not already listed, please send a message to the MyBanker admin \
              who will then be able to add the category for you

              Thanks,
              MyBanker Admin
              (The Super User)
              """ % name
    sendMessage("admin", mailSubject, mailMsg, username)
  except Exception as e:
    conn.close()
    gc.collect()
    return str(e)
  conn.close()
  gc.collect()
  return "User %s added successfully" % name

# Method to update admin password
def updatePassword(username, currentpassword, newpassword):
  if currentpassword == newpassword:
    return "Funny! Idea here is to change password not set the same password again"
  conn = mysql.connect()
  cursor = conn.cursor()
  currentPW = sha256(currentpassword).hexdigest()
  newPW = sha256(newpassword).hexdigest()
  if checkLogin(username, currentpassword):
    try:
      query = "UPDATE users SET password='%s' WHERE username='%s' AND password='%s'" % (newPW, username, currentPW)
      cursor.execute(query)
      conn.commit()
    except Exception as e:
      conn.close()
      gc.collect()
      return str(e)
    conn.close()
    gc.collect()
    return "Password for %s updated successfully" % username
  else:
    return "Operation failed! Password didn't match"

# List all users and send as dictionary
def listMybankerUsers():
  conn = mysql.connect()
  cursor = conn.cursor()
  userdict = []
  try:
    cursor.execute('SELECT * FROM users')
    userdict = cursor.fetchall()
  except Exception as e:
    conn.close()
    gc.collect()
    return None
  conn.close()
  gc.collect()
  return userdict
    
# Get list of categories
def getCategories():
  conn = mysql.connect()
  cursor = conn.cursor()
  inc_categories = []
  exp_categories = []
  try:
    cursor.execute('SELECT name FROM categories WHERE type="IN"')
    for item in cursor.fetchall():
      inc_categories.append(item[0])
    cursor.execute('SELECT name FROM categories WHERE type="EX"')
    for item in cursor.fetchall():
      exp_categories.append(item[0])
  except:
    conn.close()
    gc.collect()
    return None
  conn.close()
  gc.collect()
  return inc_categories, exp_categories

# Add a new category
def addCategory(name, cat_type):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    query = "INSERT INTO categories VALUES('%s', '%s')" % (name.upper(), cat_type)
    cursor.execute(query)
    data = cursor.fetchall()
    if len(data) is 0:
      conn.commit()
      returnstring = "New category %s added" % name
    else:
      returnstring = str(data[0])
  except Exception as e:
    conn.close()
    gc.collect()
    return str(e)
  conn.close()
  gc.collect()
  return returnstring

# Check how many accounts a user has got
def checkTotalAccounts(username):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    query = "SELECT COUNT(*) FROM accounts WHERE owner = '%s'" % username
    cursor.execute(query)
    accountsTotal = cursor.fetchone()[0]
  except Exception as e:
    conn.close()
    gc.collect()
    return None
  conn.close()
  gc.collect()
  return accountsTotal

# Add a new account
def addAccountDB(accinfo):
  conn = mysql.connect()
  cursor = conn.cursor()
  # Hardcoded to GBP at the moment. Need to revisit
  currency = "GBP"
  try:
    query = "INSERT INTO accounts VALUES('%s','%s',%s,'%s',CURDATE(),CURDATE(),'%s','%s','%s')" % \
             (accinfo['name'], accinfo['owner'], accinfo['balance'], accinfo['notes'], accinfo['exclude'], currency, accinfo['type'])
    cursor.execute(query)
    data = cursor.fetchall()
    if len(data) is 0:
      conn.commit()
      returnString = "New account %s added" % accinfo['name']
    else:
      returnString = str(data[0])
  except Exception as e:
    conn.close()
    gc.collect()
    return str(e)
  conn.close()
  gc.collect()
  return returnString

# Get accounts for dashboard table
def getAccounts(username, account="all"):
  conn = mysql.connect()
  cursor = conn.cursor()
  appendquery = ""
  if account != "all":
    appendquery = "AND name = '%s'" % account
  try:
    query = "SELECT name, balance, lastoperated, created, type, description, excludetotal FROM accounts WHERE owner = '%s' %s" % (username, appendquery)
    cursor.execute(query)
    data = cursor.fetchall()
  except Exception as e:
    conn.close()
    gc.collect()
    return None
  conn.close()
  gc.collect()
  return data

# Get account transactions
def getTransactions(username, accountname, period, year, month):
  conn = mysql.connect()
  cursor = conn.cursor()
  advQuery = limitQuery = ''

  if 'normal' in period:
    limitQuery = 'LIMIT 20'

  if 'PRE_' in period:
    if 'thisweek' in period:
      advQuery = "AND YEARWEEK(opdate) = YEARWEEK(NOW())"
    elif 'lastweek' in period:
      advQuery = "AND YEARWEEK(opdate) = YEARWEEK(NOW())-1"
    elif 'thismonth' in period:
      advQuery = "AND YEAR(opdate) = YEAR(CURDATE()) AND MONTH(opdate) = MONTH(NOW())"
    elif 'lastmonth' in period:
      advQuery = "AND YEAR(opdate) = YEAR(CURDATE()) AND MONTH(opdate) = MONTH(NOW())-1"
    elif 'last5days' in period:
      advQuery = "AND opdate >= DATE_SUB(CURDATE(), INTERVAL 5 DAY)"
    elif 'last30days' in period:
      advQuery = "AND opdate >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"
  elif 'selective' in period:
    advQuery ="AND YEAR(opdate) = %s AND MONTH(opdate) = %s" % (year, month)

  try:
    query = "SELECT opdate, description, credit, debit, category \
             FROM transactions \
             WHERE owner = '%s' AND account = '%s' %s \
             ORDER BY opdate DESC %s" \
            % (username, accountname, advQuery, limitQuery)
    cursor.execute(query)
    data = cursor.fetchall()
  except Exception as e:
    conn.close()
    gc.collect()
    return None
  conn.close()
  gc.collect()
  return data

# Get account transactions for a category
def getTransactionsForCategory(username, category, period=None, year=None, month=None):
  conn = mysql.connect()
  cursor = conn.cursor()
  advQuery = ''

  if period:
    if 'thisweek' in period:
      advQuery = "AND YEARWEEK(opdate) = YEARWEEK(NOW())"
    elif 'lastweek' in period:
      advQuery = "AND YEARWEEK(opdate) = YEARWEEK(NOW())-1"
    elif 'thismonth' in period:
      advQuery = "AND YEAR(opdate) = YEAR(CURDATE()) AND MONTH(opdate) = MONTH(NOW())"
    elif 'lastmonth' in period:
      advQuery = "AND YEAR(opdate) = YEAR(CURDATE()) AND MONTH(opdate) = MONTH(NOW())-1"
    elif 'last5days' in period:
      advQuery = "AND opdate >= DATE_SUB(CURDATE(), INTERVAL 5 DAY)"
    elif 'last30days' in period:
      advQuery = "AND opdate >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"
  else:
    advQuery ="AND YEAR(opdate) = %s AND MONTH(opdate) = %s" % (year, month)

  try:
    query = "SELECT opdate, description, credit, debit, account \
             FROM transactions \
             WHERE owner = '%s' AND category = '%s' %s \
             ORDER BY opdate DESC" \
            % (username, category, advQuery)
    cursor.execute(query)
    data = cursor.fetchall()
    if len(data) is 0:
      data = None
  except Exception as e:
    conn.close()
    gc.collect()
    return None
  conn.close()
  gc.collect()
  return data

# Check category type
def getCategoryType(category):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    query = "SELECT type FROM categories WHERE name = '%s'" % category
    cursor.execute(query)
    data = cursor.fetchone()
  except Exception as e:
    conn.close()
    gc.collect()
    return None
  conn.close()
  gc.collect()
  return data[0]

# Add transaction
def addTransactionsDB(date, notes, amount, category, account, owner):
  conn = mysql.connect()
  cursor = conn.cursor()
  credit, debit, updatetype = ["NULL", amount, "debit"]
  if getCategoryType(category) == "IN":
    credit, debit, updatetype = [amount, "NULL", "credit"]
  try:
    query = "INSERT INTO transactions VALUES('%s', '%s', '%s', %s, %s, '%s', '%s')" % \
             (date, notes, category, credit, debit, account, owner)
    cursor.execute(query)
    data = cursor.fetchall()
    if len(data) is 0:
      conn.commit()
      if updateAccounts(account, owner, amount, updatetype):
        returnString = "Transaction added successfully"
      else:
        returnString = "Failed to update accounts table. But transaction recorded"
    else:
      returnString = str(data[0])
  except Exception as e:
    conn.close()
    gc.collect()
    return str(e)
  conn.close()
  gc.collect()
  return returnString

# Get account Type
def checkAccountType(account, owner):
  conn = mysql.connect()
  cursor = conn.cursor()
  isassetAcc = True
  try:
    query = "SELECT type FROM accounts WHERE name = '%s' AND owner = '%s'" % \
             (account, owner)
    cursor.execute(query)
    data = cursor.fetchone()
  except Exception as e:
    conn.close()
    gc.collect()
    return None
  conn.close()
  gc.collect()
  if data[0] == "L":
    isassetAcc = False
  return isassetAcc

# Update Balance in Accounts table
def updateAccounts(name, owner, amount, updatetype):
  conn = mysql.connect()
  cursor = conn.cursor()
  sign,operator = ["+", "-"]
  isassetAcc = checkAccountType(name, owner)
  if not isassetAcc:
    sign = "-"
  if updatetype == "credit":
    operator = "+"
  try:
    query = "UPDATE accounts \
             SET balance = balance %s %s%s, lastoperated = CURDATE() \
             WHERE name = '%s' AND owner = '%s'" % \
             (operator, sign, amount, name, owner)
    cursor.execute(query)
    conn.commit()
  except Exception as e:
    conn.close()
    gc.collect()
    return False
  conn.close()
  gc.collect()
  return True

# Get networth of a user
def getNetworth(username):
  networth = 0.00
  accounts = getAccounts(username)
  for account in accounts:
    if 'yes' in account[6]:
      continue
    if 'L' in account[4]:
      networth = networth - float(account[1])
    else:
      networth = networth + float(account[1])
  return networth

# Get income/expense monthly/or since beginning for a user
def getInEx(username, year, period="selective"):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    if period == "selective":
      query = """
              SELECT name, COALESCE(SUM_DATA.credit, 0.00) AS credit, COALESCE(SUM_DATA.debit, 0.00) AS debit
              FROM months
              LEFT JOIN (
               SELECT MONTH(opdate) AS mnth, SUM(credit) AS credit, SUM(debit) AS debit
               FROM transactions
               WHERE owner = '%s'
                     AND YEAR(opdate) = %s
                     AND account NOT IN (%s)
                     AND category NOT IN ('TRANSFER IN','TRANSFER OUT')
               GROUP BY MONTH(opdate)
              ) SUM_DATA
              ON months.name = SUM_DATA.mnth
              ORDER BY months.name
              """ % (username, year, getIgnoredAccounts(username))
    else:
      query = """
              SELECT EXTRACT(YEAR_MONTH FROM opdate) AS period, SUM(credit) AS credit, SUM(debit) AS debit
              FROM transactions
              WHERE owner = '%s'
                    AND account NOT IN (%s)
                    AND category NOT IN ('TRANSFER IN','TRANSFER OUT')
              GROUP BY period
              ORDER BY period
              """ % (username, getIgnoredAccounts(username))
    cursor.execute(query)
    data = cursor.fetchall()
  except Exception as e:
    conn.close()
    gc.collect()
    return None
  conn.close()
  gc.collect()
  return data

# Get expense stats for a specific year
def getExpenseStats(username, year):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    query = """
            SELECT category, SUM(debit)
            FROM transactions t1
            INNER JOIN (
              SELECT name
              FROM categories
              WHERE type = 'EX' AND name NOT IN ('TRANSFER OUT')
            ) t2
            ON t1.category = t2.name
            WHERE YEAR(t1.opdate) = %s AND t1.owner = '%s' AND account NOT IN (%s)
            GROUP BY t1.category
            """ % (year, username, getIgnoredAccounts(username))
    cursor.execute(query)
    data = cursor.fetchall()
  except Exception as e:
    conn.close()
    gc.collect()
    return None
  conn.close()
  gc.collect()
  return data

# Get category stats for specific category for specific user
def getCategoryStats(username, category):
  conn = mysql.connect()
  cursor = conn.cursor()
  optype = "debit"
  if getCategoryType(category) == "IN":
    optype = "credit"
  try:
    query = """
            SELECT EXTRACT(YEAR_MONTH FROM opdate) AS period, SUM(%s) AS %s
            FROM transactions
            WHERE owner = '%s'
                  AND category = '%s'
                  AND account NOT IN (%s)
                  AND category NOT IN ('TRANSFER IN','TRANSFER OUT')
            GROUP BY period
            ORDER BY period
            """ % (optype, optype, username, category, getIgnoredAccounts(username))
    cursor.execute(query)
    data = cursor.fetchall()
  except Exception as e:
    conn.close()
    gc.collect()
    return None
  conn.close()
  gc.collect()
  return data
  return None

# Get accounts that are excluded
def getIgnoredAccounts(username):
  ignoreAccounts = []
  accounts = getAccounts(username)
  for account in accounts:
    if account[6] == 'yes':
      ignoreAccounts.append('"%s"' % account[0])
  return ",".join(ignoreAccounts)

# Do some maths to get more detailed category stats
def getDetailedCategoryStats(data):
  if data is None:
    return None
  else:
    # Find total spent in this category since beginning
    totalSpent = sum(item[1] for item in data)
    monthlyAvg = float(totalSpent) / float(len(data))
    monthlyAvg = "%.2f" % monthlyAvg
    sortedData = sorted(data, key=itemgetter(1))
    lowestPeriod = "%s %s" % (calendar.month_name[sortedData[0][0] % 100], str(sortedData[0][0])[:-2])
    lowest = [lowestPeriod, sortedData[0][1]]
    highestPeriod = "%s %s" % (calendar.month_name[sortedData[-1][0] % 100], str(sortedData[-1][0])[:-2])
    highest = [highestPeriod, sortedData[-1][1]]
    categoryStatsData = [totalSpent, monthlyAvg, highest, lowest]
    return categoryStatsData

# Get transactions for keyword search
def searchTransactions(username, keyword):
  conn = mysql.connect()
  cursor = conn.cursor()

  try:
    query = "SELECT opdate, description, credit, debit, category, account \
             FROM transactions \
             WHERE owner = '%s' AND description like '%%%s%%' \
             ORDER BY opdate DESC" \
            % (username,keyword)
    cursor.execute(query)
    data = cursor.fetchall()
  except Exception as e:
    conn.close()
    gc.collect()
    return None
  conn.close()
  gc.collect()
  return data

# Get messages for a user
def getInbox(username, msgid=None):
  conn = mysql.connect()
  cursor = conn.cursor()
  extraQuery = ""
  if msgid:
    extraQuery = "AND id = %s" % msgid
  try:
    query = "SELECT * FROM messages WHERE owner = '%s' %s ORDER BY indate DESC" % (username, extraQuery)
    cursor.execute(query)
    data = cursor.fetchall()
  except Exception as e:
    conn.close()
    gc.collect()
    return None
  conn.close()
  gc.collect()
  return data

# Get total messages and unread count for a user
def getInboxCount(username, msgtype="total"):
  conn = mysql.connect()
  cursor = conn.cursor()
  extraQuery = ""
  if msgtype == "read":
    extraQuery = "AND status = 'R'"
  elif msgtype == "unread":
    extraQuery = "AND status = 'N'"
  try:
    query = "SELECT COUNT(*) FROM messages WHERE owner = '%s' %s" % (username, extraQuery)
    cursor.execute(query)
    data = cursor.fetchone()
  except Exception as e:
    conn.close()
    gc.collect()
    return None
  conn.close()
  gc.collect()
  return data[0]

# Delete a given message
def deleteMessageDB(msgid):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    query = "DELETE FROM messages WHERE id = %s" % msgid
    cursor.execute(query)
    conn.commit()
  except Exception as e:
    conn.close()
    gc.collect()
    return None
  conn.close()
  gc.collect()
  return True 

# Upload message sent to database
def sendMessage(owner, subject, message, touser):
  conn = mysql.connect()
  cursor = conn.cursor()
  returnString = "Message successfully sent to %s" % touser
  try:
    query = "INSERT INTO messages VALUES (NULL, CURDATE(), '%s', '%s', '%s', '%s', 'N')" % (touser, subject, message.replace("\n", "<br>"), getNameofUser(owner))
    cursor.execute(query)
    data = cursor.fetchall()
    if len(data) is 0:
      conn.commit()
    else:
      returnString = str(data[0])
  except Exception as e:
    conn.close()
    gc.collect()
    return str(e)
  conn.close()
  gc.collect()
  return returnString

# Mark message read
def markMsgRead(msgid):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    query = "UPDATE messages SET status = 'R' WHERE id = %s" % msgid
    cursor.execute(query)
    conn.commit()
  except Exception as e:
    conn.close()
    gc.collect()
    return None
  conn.close()
  gc.collect()
  return True
