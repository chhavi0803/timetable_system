from models import db, User  # Import the necessary models and database session

def print_user_class_ids():
    # Query the User table to get user_id, username, and class_id
    users = db.session.query(User.user_id, User.username, User.class_id).all()

    # Print the result for each user
    for user in users:
        print(f"User ID: {user.user_id}, Username: {user.username}, Class ID: {user.class_id}")

if __name__ == "__main__":
    print_user_class_ids()  # Call the function when the script is run
