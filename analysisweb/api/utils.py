"""
This module contain help routines for the different resources
"""
import os
import subprocess
import tempfile

from jinja2 import Template
import requests

from . import celery

log_template = Template(
    "<html>\n"
    "<body>\n"
    "<code>\n"
    "{% for line in lines %}"
    "{{ line }}<br>\n"
    "{% endfor %}"
    "</code>\n"
    "</body>\n"
    "</html>\n"
)


@celery.task()
def sympathy_job(inp_file, analysis_path, sympathy_exec, log_post_url):
    """
    Run a Sympathy for data job as a Celery task in the "background"

    Parameters
    ----------
    inp_file: str
        the input config file for the analysis
    analysis_path: str
        the path to the analysis
    sympathy_exec: str
        the path to the executable that runs the analysis
    log_post_url: str
        the URL to the route where to log can be added

    Returns
    -------
    int:
        the status code of the post of the log
    """
    output = subprocess.getoutput("bash {} {} {}".format(sympathy_exec, analysis_path, inp_file))
    temp_path = tempfile.mkstemp()[1]
    with open(temp_path, "w") as f:
        f.write(log_template.render(lines=output.split("\n")))
    r = requests.post(log_post_url, files = {"log": open(temp_path, 'rb')})
    os.remove(temp_path)
    return r.status_code
