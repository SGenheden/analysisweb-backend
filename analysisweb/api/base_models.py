"""
Module containing models that the user should not extended,
and that should be considered to be the base of the backend
"""
from analysisweb.api import db


class MeasurementFile(db.Model):
    """
    A file that is part of a measurement
    """

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(64))
    path = db.Column(db.String(512))
    measurement_id = db.Column(db.Integer, db.ForeignKey("measurement.id"))


class AnalysisOutput(db.Model):
    """
    An expected output from a analysis
    """

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(64))
    type = db.Column(db.String(16))
    analysis_id = db.Column(db.Integer, db.ForeignKey("analysis.id"))


class AnalysisInput(db.Model):
    """
    An expected input to a analysis
    """

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(64))
    type = db.Column(db.String(16))
    analysis_id = db.Column(db.Integer, db.ForeignKey("analysis.id"))


class JobInput(db.Model):
    """
    A specific input to an execution of a analysis
    """

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(64))
    value = db.Column(db.String(512))
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"))


class JobTableOutput(db.Model):
    """
    A specific table output from an execution of a analysis
    """

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(64))
    path = db.Column(db.String(512))
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"))


class JobFigureOutput(db.Model):
    """
    A specific figure output from an execution of a analysis
    """

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(64))
    path = db.Column(db.String(512))
    html = db.Column(db.String(512))
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"))


class JobReport(db.Model):
    """
    A generated report of an execution of a analysis
    """

    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(512))
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"))


class Job(db.Model):
    """
    An execution of an analysis
    """

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(64))
    date = db.Column(db.DateTime, index=True)
    status = db.Column(db.String(16), index=True)
    log = db.Column(db.String(512))
    analysis_id = db.Column(db.Integer, db.ForeignKey("analysis.id"))
    measurement_id = db.Column(db.Integer, db.ForeignKey("measurement.id"))
    input = db.relationship("JobInput", backref="job")
    table_output = db.relationship("JobTableOutput", backref="job")
    figure_output = db.relationship("JobFigureOutput", backref="job")
    reports = db.relationship("JobReport", backref="job")

    def clean_up(self, session):
        for input_ in self.input:
            session.delete(input_)
        for output in self.figure_output:
            session.delete(output)
        for output in self.table_output:
            session.delete(output)
        for report in self.reports:
            session.delete(report)
