
import os
import json

from flask import request, current_app
from flask_restful.fields import Integer, List, Nested, String
from werkzeug.utils import secure_filename

from analysisweb.api import db
from analysisweb_user.models import Analysis, AnalysisInput, AnalysisOutput
from . import (ResourceBase, MetaResource, ResourceInvalidInputException,
               ResourceForbiddenActionException, ResourceNotFoundException, IDField)


class AnalysisResource(ResourceBase):

    db_table = Analysis

    analysis_inputoutput = {
        "label": String,
        "type": String
    }

    fields = {
        "id": Integer,
        "label": String,
        "syx_file": String(attribute=lambda x: "files/analyses/{}/{}".format(x.id, x.syx_file)),
        "meta_data": String,
        "input": List(Nested(analysis_inputoutput)),
        "output": List(Nested(analysis_inputoutput)),
        "jobs": List(IDField)
    }

    def get(self, id):
        """
        Receive a analysis
        ---
        summary: Find an analysis by ID
        tags:
            - analyses
        parameters:
            -   name: id
                in: path
                description: ID of an analysis to return
                required: true
                schema:
                    type: integer
        responses:
            200:
                description: successful operation
                content:
                    application/json:
                        schema:
                            $ref: "#/components/schemas/Analysis"
            400:
                description: Invalid ID supplied
            404:
                description: Analysis not found
        """
        try:
            resource = self.get_resource(id)
        except (ResourceInvalidInputException, ResourceNotFoundException) as e:
            return {"status": str(e)}, e.response_code
        return self.dump_resource(resource), 200

    def delete(self, id):
        """
        Delete an analysis
        ---
        summary: Deletes an analysis
        tags:
            - analyses
        parameters:
            -   name: id
                in: path
                description: ID of analysis to return
                required: true
                schema:
                    type: integer
        responses:
            200:
                description: Analysis deleted and returned
                content:
                    application/json:
                        schema:
                            $ref: "#/components/schemas/Analysis"
            400:
                description: Invalid ID supplied
            404:
                description: Analysis not found
            405:
                description: Cannot delete analysis associated with a job
        """
        try:
            resource = self.get_resource(id)
        except (ResourceInvalidInputException, ResourceNotFoundException) as e:
            return {"status": str(e)}, e.response_code

        try:
            return self.delete_resource(current_app.config['ANALYSIS_FILES_FOLDER'], resource)
        except ResourceForbiddenActionException as e:
            return {"status": str(e)}, e.response_code

    def put(self, id):
        """
        Update an analysis
        ---
        summary: Updates an analysis with new data
        tags:
            - analyses
        parameters:
            -   name: id
                in: path
                description: ID of analysis to return
                required: true
                schema:
                    type: integer
        requestBody:
            content:
                multipart/form-data:
                    schema:
                        properties:
                            label:
                                type: string
                            input:
                                type: array
                                items:
                                    $ref: "#/components/schemas/AnalysisInput"
                            output:
                                type: array
                                items:
                                    $ref: "#/components/schemas/AnalysisInput"
                            meta_data:
                                type: string
                            syx_file:
                                $ref: "#/components/schemas/File"
        responses:
            200:
                description: analysis updated and returned
                content:
                    application/json:
                        schema:
                            $ref: "#/components/schemas/Analysis"
            400:
                description: Invalid ID supplied or invalid input
            404:
                description: Analysis not found
        """
        try:
            resource = self.get_resource(id)
        except (ResourceInvalidInputException, ResourceNotFoundException) as e:
            return {"status": str(e)}, e.response_code

        try:
            self._update_analysis(resource)
        except ResourceInvalidInputException as e:
            return {"status": str(e)}, e.response_code
        return self.dump_resource(resource), 200

    def _update_analysis(self, resource):

        if resource.jobs:
            self._validate_form_data(resource)
            self._update_io_labels(resource)
        else:
            input_list, output_list = self._remove_previous_io(resource)
            self.add_analysis_io(resource, input_list, output_list)

            if "syx_file" in request.form:
                if len(request.files) != 1:
                    raise ResourceInvalidInputException("Missing input")
                self.set_analysis_syx(list(request.files.values())[0], resource)

        resource.label = request.form.get("label", resource.label)
        self.load_metadata(request.form.get("meta_data", None), resource)

    @staticmethod
    def add_analysis_io(analysis, input_list, output_list):
        """
        Add input and output templates to a Analysis

        Parameters
        ----------
        analysis: Analysis
            the analysis for which to add the templates
        input_list: list
            a list of serialized JSONs with the input templates
        output_list
            a list of serialized JSONs with the output templates

        Returns
        -------
        None or tuple (dict, int)
            None if successfull otherwise an error message and a return code
        """
        for item in input_list:
            item = json.loads(item.replace("'", '"'))

            if "type" not in item or "label" not in item:
                raise ResourceInvalidInputException("Missing input")
            elif item['type'].lower() not in ["value", "file"]:
                raise ResourceInvalidInputException("Input type most be either 'value' or 'file'")

            db_obj = AnalysisInput(label=item['label'], type=item['type'], analysis=analysis)
            db.session.add(db_obj)

        for item in output_list:
            item = json.loads(item.replace("'", '"'))

            if "type" not in item or "label" not in item:
                raise ResourceInvalidInputException("Missing input")
            elif item['type'].lower() not in ["table", "figure"]:
                raise ResourceInvalidInputException("Output type most be either 'table' or 'figure'")

            db_obj = AnalysisOutput(label=item['label'], type=item['type'], analysis=analysis)
            db.session.add(db_obj)

    @staticmethod
    def set_analysis_syx(file, analysis):
        """
        Set the syx file for a analysis

        Parameters
        ----------
        file: werkzeug.FileObject
            the file to upload and store
        analysis: Analysis
            the analysis for which to add the syx file

        Returns
        -------
        None or tuple (dict, int)
            None if successfull otherwise an error message and a return code
        """
        filename = secure_filename(file.filename)
        if not filename.lower().endswith('.syx'):
            raise ResourceInvalidInputException("Analysis must be a .syx-file")

        file_folder = os.path.join(current_app.config['ANALYSIS_FILES_FOLDER'], str(analysis.id))
        os.makedirs(file_folder)
        file.save(os.path.join(file_folder, filename))
        analysis.syx_file = filename

    @staticmethod
    def _remove_previous_io(resource):
        # Overwrite input and output with new data
        if "input" in request.form:
            for item in resource.input:
                db.session.delete(item)
            input_list = request.form.getlist('input')
        else:
            input_list = []

        if "output" in request.form:
            for item in resource.output:
                db.session.delete(item)
            output_list = request.form.getlist('output')
        else:
            output_list = []
        return input_list, output_list

    @staticmethod
    def _update_io_labels(resource):

        if "input" in request.form:
            for item, db_input in zip(request.form.getlist("input"), resource.input):
                item = json.loads(item.replace("'", '"'))
                if "type" in item and item["type"].lower() != db_input.type.lower():
                    raise ResourceInvalidInputException("Cannot change type of input for analysis associated with job")

                db_input.label = item.get("label", db_input.label)

        if "output" in request.form:
            for item, db_output in zip(request.form.getlist("output"), resource.output):
                item = json.loads(item.replace("'", '"'))
                if "type" in item and item["type"].lower() != db_output.type.lower():
                    raise ResourceInvalidInputException("Cannot change type of output for analysis associated with job")

                db_output.label = item.get("label", db_output.label)

    @staticmethod
    def _validate_form_data(resource):
        # Special rules apply if analysis is associated with job
        if "input" in request.form and len(request.form.getlist('input')) != len(resource.input):
            raise ResourceInvalidInputException("Cannot add/remove input for analysis associated with job")

        if "output" in request.form and len(request.form.getlist('output')) != len(resource.output):
            raise ResourceInvalidInputException("Cannot add/remove output for analysis associated with job")


class AnalysisListResource(ResourceBase):

    db_table = Analysis
    fields = AnalysisResource.fields

    def get(self):
        """
        Obtain a list of analyses
        ---
        summary: Retrieve a list of analyses
        tags:
            - analyses
        responses:
            200:
                description: OK
                content:
                    application/json:
                        schema:
                            type: array
                            items:
                                $ref: "#/components/schemas/Analysis"
        """
        return self.get_all(), 200

    def post(self):
        """
        Add a new analysis
        ---
        summary: Add a new analysis
        tags:
            - analyses
        requestBody:
            content:
                multipart/form-data:
                    schema:
                        properties:
                            label:
                                type: string
                            input:
                                type: array
                                items:
                                    $ref: "#/components/schemas/AnalysisInput"
                            output:
                                type: array
                                items:
                                    $ref: "#/components/schemas/AnalysisInput"
                            meta_data:
                                type: string
                            syx_file:
                                $ref: "#/components/schemas/File"

        responses:
            201:
                description: Analysis created
            400:
                description: Invalid input
        """

        try:
            analysis_id = self._add_analysis()
        except ResourceInvalidInputException as e:
            return {"status": str(e)}, e.response_code
        return {"status": "success", "id": analysis_id}, 201

    def _add_analysis(self):
        self._validate_form_data()
        f = Analysis(label=request.form['label'])
        db.session.add(f)
        db.session.flush()
        analysis_id = f.id
        AnalysisResource.add_analysis_io(f, request.form.getlist('input'), request.form.getlist('output'))
        self.load_metadata(request.form.get("meta_data", "{}"), f)
        AnalysisResource.set_analysis_syx(list(request.files.values())[0], f)
        db.session.commit()
        return analysis_id

    @staticmethod
    def _validate_form_data():
        if "label" not in request.form or len(request.files) != 1\
                or "input" not in request.form or "output" not in request.form:
            raise ResourceInvalidInputException("Missing input")


class AnalysisMetaResource(MetaResource):

    def get(self):
        return self.load_meta('analysis_meta.json')
