# Imports section
from flask import Flask, render_template, request, redirect, flash
from flaskext.mysql import MySQL
import fileinput

# Initialize Flask object
app = Flask(__name__)
app.secret_key = 'ilajdflkjasdlkjf;oiuqaewrlrl'

# Load configuration from file
app.config.from_object('config')

# Initialize MySQL
mysql = MySQL()
mysql.init_app(app)

# Index Route
@app.route('/')
def index():
  if app.config['INITIAL_SETUP'].lower() != 'done':
    return render_template('install_welcome.html')
  else:
    return render_template('index.html')

# Setup MyBanker Route
@app.route('/setup', methods=['GET', 'POST'])
def setup():

  # Create initial tables and load them
  conn = mysql.connect()
  cursor = conn.cursor()

  # Read all queries first
  with open ("templates/mybanker-initial.sql", "r") as myFile:
    loadQuery = myFile.readlines()

  # Load data one by one
  for query in loadQuery:
    if query:
      try:
        cursor.execute(query)
      except Exception as e:
        flash("Error while trying to populate database : %s" % str(e))
        return render_template('install_welcome.html')
      conn.commit()
  app.config['INITIAL_SETUP'] = 'done'
  
  # Update config file to mark initial setup as complete
  for line in fileinput.input("config.py", inplace=True):
    print(line.replace("pending", "done")),

  return render_template('install_complete.html')

# Main Function
if __name__ == "__main__":
  app.run(port=8002, debug=True)
