##*****************##
## Imports section ##
##*****************##
from flask import Flask, render_template, request, flash
from dbHelper import runQueriesFromFile, checkLogin
import fileinput

# Initialize Flask object
app = Flask(__name__)
app.secret_key = 'ilajdflkjasdlkjf;oiuqaewrlrl'

# Load configuration from file
app.config.from_object('config')

# Index Route 
@app.route('/')
def index():
  if app.config['INITIAL_SETUP'].lower() != 'done':
    return render_template('install_welcome.html')
  else:
    return render_template('index.html')

# Login Dashboard Route
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
  username = request.form['username']
  password = request.form['password']
  if checkLogin(username, password):
    flash("Welcome %s!" % username)
    return render_template('dashboard.html')
  else:
    flash("Invalid credentials. Please try again")
    return render_template('index.html')

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

# Main Function
if __name__ == "__main__":
  app.run(port=8002, debug=True)
