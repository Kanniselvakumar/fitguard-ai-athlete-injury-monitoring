from app import create_app, db
import os
from app.schema_sync import ensure_schema_compatibility

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Typically handled by flask-migrate, but let's create them here initially for ease
        db.create_all()
        ensure_schema_compatibility()
        os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads'), exist_ok=True)
    app.run(debug=True, port=5000)
