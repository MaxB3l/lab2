from flask import Flask
from blueprints.main import main_bp
from blueprints.api import api_bp

app = Flask(__name__)

app.register_blueprint(main_bp)      # Сайт (/, /about)
app.register_blueprint(api_bp)       # API (/api/*, /apidocs)

if __name__ == '__main__':
    app.run(debug=True)