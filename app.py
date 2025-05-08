from flask import Flask, session, g
import os
from config import Config
from models import close_db, User
import routes

def create_app():
    # Create and configure the app
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register database close function
    app.teardown_appcontext(close_db)
    
    # Register routes
    app.register_blueprint(routes.bp)
    
    # Configure before request function
    @app.before_request
    def load_logged_in_user():
        user_id = session.get('user_id')
        
        if user_id is None:
            g.user = None
        else:
            g.user = User.get_by_id(user_id)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
