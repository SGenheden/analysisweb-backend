import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import Api
from flasgger import Swagger
from flask_cors import CORS
from celery import Celery

from analysisweb import package_path
from analysisweb.api.config import Config


db = SQLAlchemy()
migrate = Migrate()
api = Api()
cors = CORS()
celery = Celery(__name__, broker=Config.CELERY_BROKER_URL)

from . import utils  # noqa

from .resources.definitions import swagger_template  # noqa

swagger = Swagger(template=swagger_template)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # This will register the API routes
    from . import routes

    db.init_app(app)
    migrate.init_app(app, db, directory=str(package_path / "migrations"))
    api.init_app(app)
    swagger.init_app(app)
    cors.init_app(app)
    celery.conf.update(app.config)

    return app
