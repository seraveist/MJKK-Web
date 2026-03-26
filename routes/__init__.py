from .main_routes import main_bp
from .api_routes import api_bp
from .upload_routes import upload_bp
from .admin_routes import admin_bp


def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(admin_bp)
