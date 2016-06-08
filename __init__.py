# Imports section
from flask import Flask, render_template, request, session, flash
from dbHelper import runQueriesFromFile, checkLogin, getNameofUser
from functools import wraps
import fileinput, gc

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
  if not request.method == "POST":
    return render_template('index.html', message="You need to login first", mtype="warning")
  username = request.form['username']
  password = request.form['password']
  if checkLogin(username, password):
    session['logged_in'] = True
    session['username'] = username
    dashboard = 'dashboard.html'
    if username == "admin":
      dashboard = 'dashboard_admin.html'
    return render_template(dashboard, loginUser=getNameofUser(username))
  else:
    return render_template('index.html', message="Invalide credentials. Please try again", mtype="danger")

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

# Main Function
if __name__ == "__main__":
  app.run(port=8002, debug=True)
