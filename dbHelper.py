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
def checkLogin(name, password):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    query = 'SELECT password FROM users where name = "%s"' % name
    cursor.execute(query)
    for row in cursor.fetchall():
      if sha256(password).hexdigest() == row[0]:
        return True
      else:
        return False
  except Exception as e:
    return False

