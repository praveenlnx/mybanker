# Imports section
from flask import Flask, render_template

# Initialize Flask object
app = Flask(__name__)

# Index Route
@app.route('/')
def index():
  return render_template('index.html')

# Main Function
if __name__ == "__main__":
  app.run(host='0.0.0.0', port='8002')
