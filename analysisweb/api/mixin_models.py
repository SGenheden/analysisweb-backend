"""
Module containing model mixin classes that the user need to use in order
to define user-defined tables for Measurements and Analyses
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr


class MetaDataException(Exception):
    pass


class MeasurementMixin(object):
    """
    A measurement of some sort that resulted in a collection of files
    This is a mixin class for a user-defined Measurement table
    """

    id = Column(Integer, primary_key=True)
    start_date = Column(DateTime, index=True)
    end_date = Column(DateTime, index=True)
    label = Column(String(64))

    @declared_attr
    def files(cls):
        return relationship("MeasurementFile", backref="measurement")

    @declared_attr
    def jobs(cls):
        return relationship("Job", backref="measurement")

    @property
    def meta_data(self):
        return {}

    @meta_data.setter
    def meta_data(self, value):
        if value:
            raise MetaDataException("Measurement table does not have any metadata")
        return

    def clean_up(self, session):
        for file in self.files:
            session.delete(file)


class AnalysisMixin(object):
    """
    A Sympathy for data analysis
    This is a mixin class for a user-defined Analysis table
    """

    id = Column(Integer, primary_key=True)
    label = Column(String(64))
    syx_file = Column(String(512))

    @declared_attr
    def input(cls):
        return relationship("AnalysisInput", backref="analysis")

    @declared_attr
    def output(cls):
        return relationship("AnalysisOutput", backref="analysis")

    @declared_attr
    def jobs(cls):
        return relationship("Job", backref="analysis")

    @property
    def meta_data(self):
        return {}

    @meta_data.setter
    def meta_data(self, value):
        if value:
            raise MetaDataException("Analysis table does not have any metadata")
        return

    def clean_up(self, session):
        for input_ in self.input:
            session.delete(input_)
        for output in self.output:
            session.delete(output)
