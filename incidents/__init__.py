import os, sys
import datetime
import io
import re
import tempfile

from flask import Flask, redirect, render_template, send_file, request, url_for
from flask_sqlalchemy import SQLAlchemy

from .lib import xlsxlib

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///incidents.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Model(object):

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.identifier())

    def identifier(self):
        return self.id

class IncidentStatus(Model, db.Model):
    __tablename__ = "incident_status"

    status = db.Column(db.Text, primary_key=True)
    sequence = db.Column(db.Integer)

    def __init__(self, status, sequence):
        self.status = status
        self.sequence = sequence

    def identifier(self):
        return self.status

class Incident(Model, db.Model):
    __tablename__ = 'incidents'

    id = db.Column(db.Integer, primary_key=True)
    one_liner = db.Column(db.Text, default="")
    description = db.Column(db.Text, default="")
    is_incident = db.Column(db.Boolean, default=0)
    is_racial = db.Column(db.Boolean, default=0)
    is_bullying = db.Column(db.Boolean, default=0)
    is_concern = db.Column(db.Boolean, default=0)
    other_type = db.Column(db.Text, default="")
    logged_on = db.Column(db.Date)
    status = db.Column(db.Text, db.ForeignKey("incident_status.status"))
    action_taken = db.Column(db.Text, default="")
    pupils = db.relationship("Pupil", secondary="incident_pupils")

    def __init__(self, one_liner="", description="", logged_on=None):
        self.one_liner = one_liner
        self.description = description
        self.is_incident = self.is_racial = self.is_bullying = self.is_concern = 0
        self.other_type = ""
        self.logged_on = logged_on or datetime.date.today()
        self.status = "Open"
        self.action_taken = ""

    def identifier(self):
        return "INC-%04d" % self.id

    def types(self):
        if self.is_incident: yield "Incident"
        if self.is_racial: yield "Racial"
        if self.is_bullying: yield "Bullying"
        if self.is_concern: yield "Concern"
        if self.other_type: yield self.other_type

    def numbered_pupils(self, min_number=4):
        """Yield pupils in turn with a minimum

        This is used to build a form with fields numbered pupil-1 etc.
        """
        n = -1
        for n, pupil_statement in enumerate(IncidentPupil.query.filter_by(incident_id=self.id)):
            yield 1 + n, pupil_statement.pupil.name, bool(pupil_statement.statement_data)
        while n < min_number - 1:
            n += 1
            yield 1 + n, "", 0

    def pupil_statements(self):
        for pupil_statement in IncidentPupil.query.filter_by(incident_id=self.id):
            yield pupil_statement.pupil, bool(pupil_statement.statement_data)

class Attachment(Model, db.Model):
    __tablename__ = "attachments"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.Text)
    data = db.Column(db.Binary)

    def __init__(self, file_object):
        self.filename = os.path.basename(file_object.filename)
        self.data = file_object.read()

    def identifier(self):
        return self.filename

class Pupil(Model, db.Model):
    __tablename__ = "pupils"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True)

    def __init__(self, name):
        self.name = name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        self_names = self._split_names()
        other_names = other._split_names()
        return self_names[::-1] < other_names[::-1]

    def _split_names(self):
        names = self.name.split()
        return names[:-1], names[-1]

    def first_name(self):
        first_name, _ = self._split_names()
        return first_name

    def last_name(self):
        _, last_name = self._split_names()
        return last_name

    def identifier(self):
        return self.name

class IncidentPupil(Model, db.Model):
    __tablename__ = "incident_pupils"

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id"), nullable=False)
    pupil_id = db.Column(db.Integer, db.ForeignKey("pupils.id"), nullable=False)
    statement_ext = db.Column(db.Text)
    statement_data = db.Column(db.Binary)

    incident = db.relationship(Incident)
    pupil = db.relationship(Pupil)

    def __repr__(self):
        return "IncidentPupil: %s - %s - %s" % (self.pupil.name, self.incident.identifier(), self.statement_ext or "(No statement)")

def update_incident_from_request(incident=None):
    if incident is None:
        incident = Incident()
    db.session.add(incident)
    incident.one_liner = request.form.get("one_liner", "")
    incident.description = request.form.get("description", "")
    incident.is_incident = request.form.get("is_incident", "") == "on"
    incident.is_racial = request.form.get("is_racial", "") == "on"
    incident.is_bullying = request.form.get("is_bullying", "") == "on"
    incident.is_concern = request.form.get("is_concern", "") == "on"
    incident.other_type = request.form.get("other_type", "")
    incident.action_taken = request.form.get("action_taken", "")

    #
    # Compare which pupils are currently linked to the incident
    # Retain those which are still listed, possibly plus a new statement
    # Remove any which are no longer listed
    #
    current_pupils = dict(
        (ip.pupil.name, ip)
            for ip in IncidentPupil.query.filter_by(incident_id=incident.id)
    )
    for i in range(1, 5):
        pupil_field = "pupil-%d" % i
        statement_field = "statement-%d" % i
        pupil_name = request.form.get(pupil_field)
        if not pupil_name: continue

        if pupil_name in current_pupils:
            incident_pupil = current_pupils.pop(pupil_name)
        else:
            pupil = Pupil.query.filter_by(name=pupil_name).first() or Pupil(name=pupil_name)
            incident_pupil = IncidentPupil(incident=incident, pupil=pupil)

        statement_file = request.files.get(statement_field)
        if statement_file and statement_file.filename:
            _, ext = os.path.splitext(statement_file.filename)
            incident_pupil.statement_ext = ext
            incident_pupil.statement_data = statement_file.read()

        db.session.add(incident_pupil)

    for orphaned in current_pupils.values():
        db.session.delete(orphaned)

    db.session.commit()
    return incident.id

def highlight_incidents(wb):
    for ws in wb:
        for cell in ws.get_cell_collection():
            if cell.data_type == "s" and re.match(r"INC-\d{4}$", cell.value):
                _, incident_id = cell.value.split("-")
                cell.hyperlink = url_for("show_incident", incident_id=int(incident_id), _external=True)
                cell.style = "Hyperlink"
    return wb

def incidents_as_excel(incidents):
    headers = [(name, str) for name in ("Incident", "Status", "Summary", "Pupils")]
    rows = []
    for incident in incidents:
        rows.append((incident.identifier(), incident.status, incident.one_liner, ", ".join(pupil.name for pupil in incident.pupils)))
    filepath = tempfile.mktemp(".xlsx")
    xlsxlib.xlsx([["Incidents", headers, rows]], filepath, callback=highlight_incidents)
    return filepath

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route("/")
def index():
    return redirect(url_for("list_incidents"))

@app.route("/finish")
def finish():
    shutdown_server()
    return "Shutting down..."

@app.route("/incidents", methods=["GET"])
def list_incidents():
    incidents = Incident.query.all()
    return render_template("incidents.html", title="Incidents", incidents=Incident.query.all())

@app.route("/export_incidents", methods=["GET"])
def export_incidents():
    incidents = Incident.query.all()
    filepath = incidents_as_excel(incidents)
    return send_file(filepath, as_attachment=True, cache_timeout=-1)

@app.route("/incident/<incident_id>", methods=["GET"])
def show_incident(incident_id):
    incident = Incident.query.get(incident_id)
    title = "%s: %s" % (incident.identifier(), incident.one_liner)
    return render_template("incident.html", title=title, incident=incident)

@app.route("/incident/<incident_id>/pupil/<pupil_id>/statement", methods=["GET"])
def show_statement(incident_id, pupil_id):
    incident_pupil = IncidentPupil.query.filter_by(incident_id=incident_id, pupil_id=pupil_id).first()
    filename = "%05d%s" % (incident_pupil.id, incident_pupil.statement_ext)
    return send_file(
        io.BytesIO(incident_pupil.statement_data),
        as_attachment=True, attachment_filename=filename
    )

@app.route("/incident/<incident_id>/edit", methods=["GET"])
def edit_incident(incident_id):
    incident = Incident.query.get(incident_id)
    title = "Edit %s" % (incident.identifier())
    return render_template("edit_incident.html", title=title, incident=incident)

@app.route("/incident/<incident_id>", methods=["POST", "PUT"])
def update_incident(incident_id):
    if "PUT" not in (request.method, request.form.get("_method", "")):
        raise MethodNotAllowed(["PUT"])
    if request.form.get("submit", "") == "Update":
        incident = Incident.query.get(incident_id)
        incident_id = update_incident_from_request(incident)
    return redirect(url_for("show_incident", incident_id=incident_id), code=302)

@app.route("/incidents/new", methods=["GET"])
def new_incident():
    return render_template("edit_incident.html", title="New Incident", incident=Incident())

@app.route("/incidents", methods=["POST"])
def create_incident():
    if request.form.get("submit", "") == "Update":
        incident_id = update_incident_from_request()
        return redirect(url_for("show_incident", incident_id=incident_id), code=302)
    else:
        return redirect(url_for("list_incidents"), code=302)

@app.route("/attachment/<attachment_id>", methods=["GET"])
def show_attachment(attachment_id):
    attachment = Attachment.query.get(attachment_id)
    return send_file(io.BytesIO(attachment.data), attachment_filename=attachment.filename)

