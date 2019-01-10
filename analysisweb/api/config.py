import os

from analysisweb_user.config import UserConfig


class Config(UserConfig):
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MEASUREMENT_FILES_FOLDER = os.path.join(UserConfig.UPLOAD_FOLDER, "measurement")
    ANALYSIS_FILES_FOLDER = os.path.join(UserConfig.UPLOAD_FOLDER, "analysis")
    JOB_FILES_FOLDER = os.path.join(UserConfig.UPLOAD_FOLDER, "job")

    SECRET_KEY = "you-will-never-guess"  # for developement
