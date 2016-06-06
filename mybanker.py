# Imports section
from flask import Flask, render_template

# Initialize Flask object
app = Flask(__name__)

# Load configuration from file
app.config.from_object('config')

# Index Route
@app.route('/')
def index():
  if app.config['INITIAL_SETUP'].lower() != 'done':
    return render_template('install_welcome.html')
  else:
    return render_template('index.html')

# Initial Install Route
@app.route('/setup', methods=['GET', 'POST'])
def setup():
  return render_template('install_welcome_details.html')

# Main Function
if __name__ == "__main__":
  app.run(port=8002, debug=True)
