
import datetime
import json
import os

from flask import request, current_app
from flask_restful.fields import Integer, List, Raw, String, Nested
from werkzeug.utils import secure_filename

from analysisweb.api import db
from analysisweb_user.models import Measurement, Analysis, Job, JobInput, JobFigureOutput, JobTableOutput, JobReport
from . import (ResourceBase, ResourceInvalidInputException,
               ResourceForbiddenActionException, ResourceNotFoundException, IDField)
import app.utils as utils


class JobInputFile(Raw):
    def format(self, value):
        val = value.value
        if os.path.exists(os.path.join(current_app.config['JOB_FILES_FOLDER'], str(value.job_id), "input", val)):
            val = "files/job/{}/input/{}".format(value.job_id, val)
        return val


class JobReportFile(Raw):
    def format(self, value):
        return "files/job/{}/reports/{}".format(value.job_id, value.path)


def make_input_value(value):
    val = value.value
    if os.path.exists(os.path.join(current_app.config['JOB_FILES_FOLDER'], str(value.job_id), "input", val)):
        val = "files/job/{}/input/{}".format(value.job_id, val)
    return val


class JobResource(ResourceBase):

    db_table = Job

    job_inputfile = {
        "label": String,
        "value": String(attribute=lambda x: make_input_value(x))
    }

    job_outputfile = {
        "label": String,
        "path": String(attribute=lambda x: "files/job/{}/output/{}".format(x.job.id, x.path))
    }

    fields = {
        "id": Integer,
        "label": String,
        "date": String(attribute=lambda x: x.date.strftime("%Y-%m-%d %H:%M")),
        "status": String,
        "log": String(attribute=lambda x: "files/job/{}/{}".format(x.id, x.log) if x.log else ""),
        "analysis": IDField,
        "measurement": IDField,
        "input": List(Nested(job_inputfile)),
        "table_output": List(Nested(job_outputfile)),
        "figure_output": List(Nested(job_outputfile)),
        "reports": List(JobReportFile)
    }

    def get(self, id):
        """
        Receive a job
        ---
        summary: Find a job by ID
        tags:
            - jobs
        parameters:
            -   name: id
                in: path
                description: ID of job to return
                required: true
                schema:
                    type: integer
        responses:
            200:
                description: successful operation
                content:
                    application/json:
                        schema:
                            $ref: "#/components/schemas/Job"
            400:
                description: Invalid ID supplied
            404:
                description: Job not found
        """
        try:
            resource = self.get_resource(id)
        except (ResourceInvalidInputException, ResourceNotFoundException) as e:
            return {"status": str(e)}, e.response_code
        return self.dump_resource(resource), 200

    def delete(self, id):
        """
        Delete a job
        ---
        summary: Deletes a job
        tags:
            - jobs
        parameters:
            -   name: id
                in: path
                description: ID of job to delete
                required: true
                schema:
                    type: integer
        responses:
            200:
                description: Job deleted and returned
                content:
                    application/json:
                        schema:
                            $ref: "#/components/schemas/Job"
            400:
                description: Invalid ID supplied
            404:
                description: Job not found
        """
        try:
            resource = self.get_resource(id)
        except (ResourceInvalidInputException, ResourceNotFoundException) as e:
            return {"status": str(e)}, e.response_code

        try:
            return self.delete_resource(current_app.config['JOB_FILES_FOLDER'], resource)
        except ResourceForbiddenActionException as e:
            return {"status": str(e)}, e.response_code


class JobListResource(ResourceBase):

    db_table = Job
    fields = JobResource.fields

    def get(self):
        """
        Obtain a list of executed jobs
        ---
        summary: Retrieve a list of executed jobs
        tags:
            - jobs
        responses:
            200:
                description: OK
                content:
                    application/json:
                        schema:
                            type: array
                            items:
                                $ref: "#/components/schemas/Job"
        """
        return self.get_all(), 200

    def post(self):
        """
        Add a new job to the queue
        ---
        summary: Add a new job to the queue
        tags:
            - jobs
        requestBody:
            content:
                multipart/form-data:
                    schema:
                        properties:
                            label:
                                type: string
                            measurement:
                                type: integer
                            analysis:
                                type: integer
                            input:
                                type: array
                                items:
                                    type: string
                            files:
                                type: array
                                items:
                                    $ref: "#/components/schemas/File"
        responses:
            202:
                description: Job was successfully added to the queue
            400:
                description: Id of measurement or analysis is invalid, or invalid input
            404:
                description: Id of measurement or analysis is not existing
        """
        try:
            job_id = self._add_job()
        except ResourceInvalidInputException as e:
            db.session.rollback()
            return {"status": str(e)}, e.response_code
        return {"status": "success", "id": job_id}, 202

    def _add_job(self):
        self._validate_form_data()
        if 'measurement' in request.form:
            measurement = self.get_resource(request.form['measurement'], Measurement)
        else:
            measurement = None
        analysis = self.get_resource(request.form['analysis'], Analysis)
        self._validate_job_input(analysis, measurement)

        job = Job(label=request.form['label'], measurement=measurement, analysis=analysis)
        db.session.add(job)
        db.session.flush()
        job_id = job.id

        for f in ['reports', 'output', 'input']:
            file_folder = os.path.join(current_app.config['JOB_FILES_FOLDER'], str(job_id), f)
            os.makedirs(file_folder)
        self._add_job_input(job, analysis, file_folder)

        job.status = "SUBMITTED"
        job.date = datetime.datetime.now()
        db.session.commit()
        self._initiate_job(job, analysis, measurement)
        return job_id

    @staticmethod
    def _add_job_input(job, analysis, path):
        input_list = request.form.getlist('input')
        files = request.files
        for analysis_input, item in zip(analysis.input, input_list):
            if item.startswith("$file:"):
                file_key = item[6:]
                file = files.get(file_key)
                if file:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(path, filename))
                    value = filename
                else:
                    value = file_key
            else:
                value = item
            db_obj = JobInput(value=value, job=job, label=analysis_input.label)
            db.session.add(db_obj)

    @staticmethod
    def _initiate_job(job, analysis, measurement):
        base_folder = os.path.join(current_app.config['JOB_FILES_FOLDER'], str(job.id))
        inp = JobListResource._make_input_json(job, analysis, measurement)
        inp_file = os.path.join(base_folder, "inp.json")
        with open(inp_file, 'w') as f:
            json.dump(inp, f)
        syx_file = os.path.join(current_app.config['ANALYSIS_FILES_FOLDER'], str(analysis.id), analysis.syx_file)
        post_url = current_app.config['SERVER_URL'] + "job/{}/log".format(job.id)
        utils.sympathy_job.delay(inp_file, syx_file, current_app.config['SYMPATHY_EXEC'], post_url)

    @staticmethod
    def _make_input_json(job, analysis, measurement):
        # TODO replace actual paths to the upload folder with URLs to the server
        input = []
        for job_input, analysis_input in zip(job.input, analysis.input):
            if analysis_input.type == "value":
                value = job_input.value
            else:
                if job_input.value.startswith("$measurement"):
                    value = ""
                    for f in measurement.files:
                        if f.label == analysis_input.label:
                            value = os.path.join(current_app.config['MEASUREMENT_FILES_FOLDER'],
                                                 str(measurement.id), f.path)
                            break
                else:
                    value = os.path.join(current_app.config['JOB_FILES_FOLDER'],
                                         str(job.id), "input", job_input.value)
            input.append({"label": analysis_input.label, "value": value})
        output = [{"type": o.type, "label": o.label} for o in analysis.output]
        post_url = current_app.config['SERVER_URL'] + "job/{}/output".format(job.id)
        return {
            "input": input,
            "output": output,
            "job_id": job.id,
            "post_url": post_url
        }

    @staticmethod
    def _validate_form_data():
        if "label" not in request.form or "analysis" not in request.form\
                or "input" not in request.form:
            raise ResourceInvalidInputException("Missing input")

    @staticmethod
    def _validate_job_input(analysis, measurement):
        ninput = len(request.form.getlist('input'))
        nexpected = len(analysis.input)
        if ninput != nexpected:
            raise ResourceInvalidInputException(
                "Too few or too many input values, expecting {} but got {}".format(nexpected, ninput))

        input_list = request.form.getlist('input')
        if measurement is not None:
            measurement_labels = [f.label for f in measurement.files]
        else:
            measurement_labels = []

        for i, (analysis_input, item) in enumerate(zip(analysis.input, input_list)):
            is_ref = item.startswith("$")
            if analysis_input.type.lower() is "value" and is_ref:
                raise ResourceInvalidInputException(
                    "Expected a 'value' input at position {} but found a reference".format(i))
            if item.startswith('$measurement') and measurement is None:
                raise ResourceInvalidInputException(
                    "Found a reference to a measurement in input but no measurement given")
            elif item.startswith('$measurement') and analysis_input.label not in measurement_labels:
                raise ResourceInvalidInputException(
                    "The analysis input label '{}' does not correspond to  any measurement label".format(analysis_input.label))


class JobOutputResource(ResourceBase):

    db_table = Job
    fields = JobResource.fields

    def post(self, id):
        """
        Add output files to a job
        ---
        summary: Add output files to a job
        tags:
            - jobs
        parameters:
            -   name: id
                in: path
                description: ID of job to add the output
                required: true
                schema:
                    type: integer
        requestBody:
            content:
                multipart/form-data:
                    schema:
                        properties:
                            files:
                                type: array
                                items:
                                    $ref: "#/components/schemas/File"
        responses:
            200:
                description: Output was successfully added
                content:
                    application/json:
                        schema:
                            $ref: "#/components/schemas/Job"
            400:
                description: Invalid input
            404:
                description: ID of job not found
            405:
                description: Job does already have output
        """
        try:
            resource = self.get_resource(id)
        except (ResourceInvalidInputException, ResourceNotFoundException) as e:
            return {"status": str(e)}, e.response_code

        try:
            self._add_output(resource)
        except (ResourceInvalidInputException, ResourceForbiddenActionException) as e:
            return {"status": str(e)}, e.response_code
        return self.dump_resource(resource), 200

    def _add_output(self, resource):

        if len(resource.table_output) != 0 or len(resource.figure_output) != 0:
            raise ResourceForbiddenActionException("Job does already have output")
        if not request.files:
            raise ResourceInvalidInputException("No output files in request body")

        types = {o.label: o.type for o in resource.analysis.output}
        file_folder = os.path.join(current_app.config['JOB_FILES_FOLDER'], str(resource.id), "output")
        for output_label, output_type in types.items():
            if output_type == "table":
                self._add_table(resource, output_label, file_folder)
            elif output_type == "figure":
                self._add_figure(resource, output_label, file_folder)
        db.session.commit()

    @staticmethod
    def _add_figure(job, label, path):
        if label + ".fig" not in request.files or label + ".html" not in request.files:
            raise ResourceInvalidInputException("Missing file with label {}".format(label))
        file_fig = request.files[label + ".fig"]
        file_html = request.files[label + ".html"]
        filename_fig = secure_filename(file_fig.filename)
        filename_html = secure_filename(file_html.filename)
        if not filename_fig.lower().endswith(".png") or not filename_html.lower().endswith(".html"):
            raise ResourceInvalidInputException(
                "Unexpected file extension '{}' "
                "for '{}' for figure type".format(filename_fig[-4:], filename_html[-5:]))
        file_fig.save(os.path.join(path, filename_fig))
        file_html.save(os.path.join(path, filename_html))
        f = JobFigureOutput(path=filename_fig, html=filename_html, label=label, job=job)
        db.session.add(f)

    @staticmethod
    def _add_table(job, label, path):
        if label not in request.files:
            raise ResourceInvalidInputException("Missing file with label {}".format(label))
        file = request.files[label]
        filename = secure_filename(file.filename)
        if not filename.lower().endswith(".csv"):
            raise ResourceInvalidInputException(
                "Unexpected file extension '{}' for table type".format(filename[-4:]))
        file.save(os.path.join(path, filename))
        f = JobTableOutput(path=filename, label=label, job=job)
        db.session.add(f)


class JobReportResource(ResourceBase):

    db_table = Job
    fields = JobResource.fields

    def post(self, id):
        """
        Add a report to a job
        ---
        summary: Add a report to a job
        tags:
            - jobs
        requestBody:
            content:
                multipart/form-data:
                    schema:
                        $ref: "#/components/schemas/File"
        responses:
            200:
                description: Report was sucessfully added
                content:
                    application/json:
                        schema:
                            $ref: "#/components/schemas/Job"
            400:
                description: Invalid input
            404:
                description: ID of job not found
        """

        try:
            resource = self.get_resource(id)
        except (ResourceInvalidInputException, ResourceNotFoundException) as e:
            return {"status": str(e)}, e.response_code

        try:
            self._add_report(resource)
        except ResourceInvalidInputException as e:
            return {"status": str(e)}, e.response_code
        return self.dump_resource(resource), 200

    @staticmethod
    def _add_report(resource):
        if not request.files:
            raise ResourceInvalidInputException("No reports in request body")

        file_folder = os.path.join(current_app.config['JOB_FILES_FOLDER'], str(resource.id), "reports")
        lookup = [report.path for report in resource.reports]
        for label, file in request.files.items():
            if file:
                file.save(os.path.join(file_folder, label))
                if label not in lookup:
                    f = JobReport(path=label, job=resource)
                    db.session.add(f)
        db.session.commit()


class JobLogResource(ResourceBase):

    db_table = Job
    fields = JobResource.fields

    def post(self, id):
        """
        Add a log to a job
        ---
        summary: Add a log to a job
        tags:
            - jobs
        requestBody:
            content:
                multipart/form-data:
                    schema:
                        $ref: "#/components/schemas/File"
        responses:
            200:
                description: Log was sucessfully added
                content:
                    application/json:
                        schema:
                            $ref: "#/components/schemas/Job"
            400:
                description: Invalid input
            404:
                description: ID of job not found
        """

        try:
            resource = self.get_resource(id)
        except (ResourceInvalidInputException, ResourceNotFoundException) as e:
            return {"status": str(e)}, e.response_code

        try:
            self._add_job(resource)
        except ResourceInvalidInputException as e:
            return {"status": str(e)}, e.response_code
        return self.dump_resource(resource), 200

    @staticmethod
    def _add_job(resource):
        if not request.files:
            raise ResourceInvalidInputException("No file in request body")
        if len(request.files) > 1:
            raise ResourceInvalidInputException("Only one log can be added to the job")
        if resource.log:
            raise ResourceInvalidInputException("This job already have a job")

        file_folder = os.path.join(current_app.config['JOB_FILES_FOLDER'], str(resource.id))
        file = request.files['log']
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(file_folder, "log.html"))
            resource.log = "log.html"
        resource.status = "COMPLETED"
        db.session.commit()
