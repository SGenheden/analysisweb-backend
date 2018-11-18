
import os

from analysisweb_user.config import UserConfig


class Config(UserConfig):
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MEASUREMENT_FILES_FOLDER = os.path.join(UserConfig.UPLOAD_FOLDER, "measurement")
    FLOW_FILES_FOLDER = os.path.join(UserConfig.UPLOAD_FOLDER, "flow")
    JOB_FILES_FOLDER = os.path.join(UserConfig.UPLOAD_FOLDER, "job")

    SECRET_KEY = 'you-will-never-guess' # for developement



