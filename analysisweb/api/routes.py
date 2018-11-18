
from . import api

from analysisweb.api.resources.measurements import MeasurementResource, MeasurementListResource, MeasurementMetaResource
from analysisweb.api.resources.flows import FlowResource, FlowListResource, FlowMetaResource
from analysisweb.api.resources.jobs import JobResource, JobListResource, JobOutputResource, JobReportResource, JobLogResource

api.add_resource(MeasurementListResource, '/measurements')
api.add_resource(MeasurementResource, '/measurement/<id>')
api.add_resource(MeasurementMetaResource, '/measurements/meta')
api.add_resource(FlowListResource, '/flows')
api.add_resource(FlowResource, '/flow/<id>')
api.add_resource(FlowMetaResource, '/flows/meta')
api.add_resource(JobListResource, '/jobs')
api.add_resource(JobResource, '/job/<id>')
api.add_resource(JobOutputResource, '/job/<id>/output')
api.add_resource(JobReportResource, '/job/<id>/report')
api.add_resource(JobLogResource, '/job/<id>/log')
