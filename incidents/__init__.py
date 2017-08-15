import os, sys
import datetime
import io

from flask import Flask, redirect, render_template, send_file, request, url_for
from flask_sqlalchemy import SQLAlchemy

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

incident_pupils = db.Table(
    "incident_pupils",
    db.Column("incident_id", db.Integer, db.ForeignKey("incidents.id")),
    db.Column("pupil_id", db.Integer, db.ForeignKey("pupils.id"))
)

class Incident(Model, db.Model):
    __tablename__ = 'incidents'

    id = db.Column(db.Integer, primary_key=True)
    one_liner = db.Column(db.Text)
    description = db.Column(db.Text)
    is_incident = db.Column(db.Boolean)
    is_racial = db.Column(db.Boolean)
    is_bullying = db.Column(db.Boolean)
    is_concern = db.Column(db.Boolean)
    other_type = db.Column(db.Text)
    logged_on = db.Column(db.Date)
    status = db.Column(db.Text, db.ForeignKey("incident_status.status"))
    action_taken = db.Column(db.Text)
    attachments = db.relationship("Attachment", backref="incident")
    pupils = db.relationship("Pupil", secondary=incident_pupils, backref=db.backref("incidents"))

    def __init__(self, one_liner="", description="", attachments=[], logged_on=None):
        self.one_liner = one_liner
        self.description = description
        self.attachments = attachments
        self.logged_on = logged_on or datetime.date.today()
        self.status = "Open"

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
        for n, pupil in enumerate(self.pupils):
            yield 1 + n, pupil
        while n < min_number - 1:
            n += 1
            yield 1 + n, ""

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
    incident.pupils.clear()
    pupil_names = [value for (name, value) in request.form.items() if name.startswith("pupil-") and value]
    incident.pupils = [Pupil.query.filter_by(name=name).first() or Pupil(name=name) for name in pupil_names]
    db.session.commit()
    return incident.id

class Attachment(Model, db.Model):
    __tablename__ = "attachments"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.Text)
    data = db.Column(db.Binary)
    incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id"))

    def __init__(self, filepath):
        with open(filepath, "rb") as f:
            self.data = f.read()
        self.filename = os.path.basename(filepath)

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

@app.route("/")
def index():
    return redirect(url_for("list_incidents"))

@app.route("/incidents", methods=["GET"])
def list_incidents():
    incidents = Incident.query.all()
    return render_template("incidents.html", title="Incidents", incidents=Incident.query.all())

@app.route("/incident/<incident_id>", methods=["GET"])
def show_incident(incident_id):
    incident = Incident.query.get(incident_id)
    title = "%s: %s" % (incident.identifier(), incident.one_liner)
    return render_template("show_incident.html", title=title, incident=incident)

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
