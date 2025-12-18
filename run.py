from app import create_app
from app.database import db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Import seeds inside app context
        from seeds import initialize_default_data, create_default_admin
        
        # Create all tables
        db.create_all()
        
        # Initialize default data
        initialize_default_data()
        create_default_admin()
    
    app.run(debug=True)