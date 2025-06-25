from app import create_app

app = create_app('development')  # Pass string instead of class

if __name__ == "__main__":
    app.run()