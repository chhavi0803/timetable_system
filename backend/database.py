from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def init_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///timetable_system.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        # Delete the database file if it exists
        # db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        # if os.path.exists(db_path):
        #     os.remove(db_path)
        #     print(f"Deleted existing database: {db_path}")

        # Create all tables from scratch
        db.create_all()
        print(f"Created new database")