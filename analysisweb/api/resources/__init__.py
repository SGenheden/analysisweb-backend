import json
import os
import shutil

from flask import current_app, jsonify
from flask_restful import Resource, marshal
from flask_restful.fields import Raw

import analysisweb_user
from analysisweb.api import db
from analysisweb_user.models import MetaDataException


class IDField(Raw):
    def format(self, value):
        return {"id": value.id, "label": value.label}


class ResourceInvalidInputException(Exception):
    response_code = 400

    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
        db.session.rollback()


class ResourceNotFoundException(Exception):
    response_code = 404


class ResourceForbiddenActionException(Exception):
    response_code = 405


class ResourceBase(Resource):

    db_table = None
    fields = None

    def get_all(self):
        return [marshal(m, self.fields) for m in self.db_table.query.all()]

    def get_resource(self, id_, table=None):
        table = table or self.db_table
        try:
            id_ = int(id_)
        except ValueError:
            raise ResourceInvalidInputException("Item ID is not a valid integer")

        try:
            resource = table.query.get(id_)
        except Exception as e:  # noqa
            raise ResourceNotFoundException(
                "Item could not be retrieved from database: {}".format(e)
            )

        if resource is None:
            raise ResourceNotFoundException("Item does not exists in the database")
        else:
            return resource

    def delete_resource(self, base_path, db_resource):
        if hasattr(db_resource, "jobs") and db_resource.jobs:
            raise ResourceForbiddenActionException(
                "Item cannot be removed because it is associated with a job"
            )
        json_resource = self.dump_resource(db_resource)
        shutil.rmtree(os.path.join(base_path, str(db_resource.id)))
        db_resource.clean_up(db.session)
        db.session.delete(db_resource)
        db.session.commit()
        return json_resource

    def dump_resource(self, db_resource):
        return marshal(db_resource, self.fields)

    @staticmethod
    def load_metadata(metadata, db_resource):
        if metadata is None:
            return

        meta_data = json.loads(metadata)

        if meta_data:
            try:
                db_resource.meta_data = meta_data
            except MetaDataException as e:
                raise ResourceInvalidInputException("Invalid metadata: {}".format(e))


class MetaResource(Resource):
    @staticmethod
    def load_meta(filename):
        path = os.path.abspath(os.path.dirname(analysisweb_user.__file__))
        meta_filename = os.path.join(path, filename)
        with open(meta_filename, "r") as f:
            meta = json.load(f)
        current_app.config[
            "JSON_SORT_KEYS"
        ] = False  # This is not recommended by Flask but done here locally
        meta = jsonify(meta)
        current_app.config["JSON_SORT_KEYS"] = True
        return meta
