from flask import Flask
from routes import init_routes
from database import init_db

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
app.secret_key = 'supersecretkey'

# Initialize the database
init_db(app)

# Initialize routes
init_routes(app)

if __name__ == '__main__':
    app.run(debug=True)