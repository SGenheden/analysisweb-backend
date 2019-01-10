import os

from dateutil.parser import parse as date_parser
from flask import request, current_app
from flask_restful.fields import Integer, List, Nested, Raw, String
from werkzeug.utils import secure_filename

from analysisweb.api import db
from analysisweb_user.models import Measurement, MeasurementFile
from . import (
    ResourceBase,
    MetaResource,
    ResourceInvalidInputException,
    ResourceForbiddenActionException,
    ResourceNotFoundException,
    IDField,
)


class MeasurementResource(ResourceBase):

    db_table = Measurement

    measurement_file = {
        "label": String,
        "path": String(
            attribute=lambda x: "files/measurement/{}/{}".format(
                x.measurement_id, x.path
            )
        ),
    }

    fields = {
        "id": Integer,
        "label": String,
        "start_date": String,
        "end_date": String,
        "meta_data": Raw,
        "files": List(Nested(measurement_file)),
        "jobs": List(IDField),
    }

    def get(self, id_):
        """
        Receive a measurement
        ---
        summary: Find a measurement by ID
        tags:
            - measurements
        parameters:
            -   name: id
                in: path
                description: ID of measurement to return
                required: true
                schema:
                    type: integer
        responses:
            200:
                description: successful operation
                content:
                    application/json:
                        schema:
                            $ref: "#/components/schemas/Measurement"
            400:
                description: Invalid ID supplied
            404:
                description: Measurement not found
        """
        try:
            resource = self.get_resource(id_)
        except (ResourceInvalidInputException, ResourceNotFoundException) as e:
            return {"status": str(e)}, e.response_code
        return self.dump_resource(resource), 200

    def delete(self, id_):
        """
        Delete a measurement
        ---
        summary: Deletes a measurement
        tags:
            - measurements
        parameters:
            -   name: id
                in: path
                description: ID of measurement to return
                required: true
                schema:
                    type: integer
        responses:
            200:
                description: Measurement deleted and returned
                content:
                    application/json:
                        schema:
                            $ref: "#/components/schemas/Measurement"
            400:
                description: Invalid ID supplied
            404:
                description: Measurement not found
            405:
                description: Cannot delete measurement associated with a job
        """
        try:
            resource = self.get_resource(id_)
        except (ResourceInvalidInputException, ResourceNotFoundException) as e:
            return {"status": str(e)}, e.response_code

        try:
            return self.delete_resource(
                current_app.config["MEASUREMENT_FILES_FOLDER"], resource
            )
        except ResourceForbiddenActionException as e:
            return {"status": str(e)}, e.response_code

    def put(self, id_):
        """
        Update the basic information about a measurement
        ---
        summary: Updates a measurement with new data
        tags:
            - measurements
        parameters:
            -   name: id
                in: path
                description: ID of measurement to return
                required: true
                schema:
                    type: integer
        requestBody:
            content:
                multipart/form-data:
                    schema:
                        properties:
                            start_date:
                              type: string
                              format: date-time
                            end_date:
                                type: string
                                format: date-time
                            label:
                                type: string
                            meta_data:
                                type: string
        responses:
            200:
                description: Measurement updated and returned
                content:
                    application/json:
                        schema:
                            $ref: "#/components/schemas/Measurement"
            400:
                description: Invalid ID supplied or invalid input
            404:
                description: Measurement not found
        """

        try:
            resource = self.get_resource(id_)
        except (ResourceInvalidInputException, ResourceNotFoundException) as e:
            return {"status": str(e)}, e.response_code

        try:
            self._update_measurement(resource)
        except ResourceInvalidInputException as e:
            return {"status": str(e)}, e.response_code
        return self.dump_resource(resource), 200

    def _update_measurement(self, resource):
        start_date, end_date = self.parse_dates(
            str(resource.start_date), str(resource.end_date)
        )
        resource.start_date = start_date
        resource.end_date = end_date
        resource.label = request.form.get("label", resource.label)
        self.load_metadata(request.form.get("meta_data", "{}"), resource)
        db.session.commit()

    @staticmethod
    def parse_dates(start=None, end=None):
        try:
            start_date = date_parser(request.form.get("start_date", start))
            end_date = date_parser(request.form.get("end_date", end))
        except ValueError as e:
            raise ResourceInvalidInputException(str(e))

        if end_date < start_date:
            raise ResourceInvalidInputException("end date < start date")
        return start_date, end_date


class MeasurementListResource(ResourceBase):

    db_table = Measurement
    fields = MeasurementResource.fields

    def get(self):
        """
        Obtain a list of measurements
        ---
        summary: Retrieve a list of measurements
        tags:
            - measurements
        responses:
            200:
                description: OK
                content:
                    application/json:
                        schema:
                            type: array
                            items:
                                $ref: "#/components/schemas/Measurement"
        """
        return self.get_all(), 200

    def post(self):
        """
        Add a new measurement
        ---
        summary: Add a new measurement
        tags:
            - measurements
        requestBody:
            content:
                multipart/form-data:
                    schema:
                        properties:
                            start_date:
                                type: string
                                format: date-time
                            end_date:
                                type: string
                                format: date-time
                            label:
                                type: string
                            meta_data:
                                type: string
                            files:
                                type: array
                                items:
                                    $ref: "#/components/schemas/File"
        responses:
            201:
                description: Measurement created
            400:
                description: Invalid input
        """
        try:
            measurement_id = self._add_measurement()
        except ResourceInvalidInputException as e:
            return {"status": str(e)}, e.response_code
        return {"status": "success", "id": measurement_id}, 201

    def _add_measurement(self):
        self._validate_form_data()
        start_date, end_date = MeasurementResource.parse_dates()
        m = Measurement(
            start_date=start_date, end_date=end_date, label=request.form["label"]
        )
        db.session.add(m)
        db.session.flush()
        measurement_id = m.id
        self.load_metadata(request.form.get("meta_data", "{}"), m)
        file_folder = os.path.join(
            current_app.config["MEASUREMENT_FILES_FOLDER"], str(measurement_id)
        )
        os.makedirs(file_folder)
        print(request.files)
        self._add_measurement_files(m, request.files.items(), file_folder)
        db.session.commit()
        return measurement_id

    @staticmethod
    def _add_measurement_files(measurement, file_list, path):
        """
        Add files to a measurement

        Parameters
        ----------
        measurement: Measurement
            the measurement to which add the files
        file_list: list of werkzeug.Files
            the given list of files
        path: str
            the folder in which to upload the files to
        """
        for label, file in file_list:
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(path, filename))
                f = MeasurementFile(label=label, path=filename, measurement=measurement)
                db.session.add(f)

    @staticmethod
    def _validate_form_data():
        if (
            "start_date" not in request.form
            or "end_date" not in request.form
            or "label" not in request.form
            or not request.files
        ):
            raise ResourceInvalidInputException("Missing input")


class MeasurementMetaResource(MetaResource):
    def get(self):
        return self.load_meta("user_meta.json")
