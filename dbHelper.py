# Import Section
from flask import Flask
from flask import current_app as app
from flaskext.mysql import MySQL
from hashlib import sha256
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
    print query
    cursor.execute(query)
    conn.commit()
  except Exception as e:
    conn.close()
    gc.collect()
    return str(e)
  conn.close()
  gc.collect()
  return "User %s added successfully" % name
