
from . import api

from analysisweb.api.resources.measurements import MeasurementResource, MeasurementListResource, MeasurementMetaResource
from analysisweb.api.resources.analyses import AnalysisResource, AnalysisListResource, AnalysisMetaResource
from analysisweb.api.resources.jobs import JobResource, JobListResource, JobOutputResource, JobReportResource, JobLogResource

api.add_resource(MeasurementListResource, '/measurements')
api.add_resource(MeasurementResource, '/measurement/<id>')
api.add_resource(MeasurementMetaResource, '/measurements/meta')
api.add_resource(AnalysisListResource, '/analyses')
api.add_resource(AnalysisResource, '/analysis/<id>')
api.add_resource(AnalysisMetaResource, '/analysis/meta')
api.add_resource(JobListResource, '/jobs')
api.add_resource(JobResource, '/job/<id>')
api.add_resource(JobOutputResource, '/job/<id>/output')
api.add_resource(JobReportResource, '/job/<id>/report')
api.add_resource(JobLogResource, '/job/<id>/log')
