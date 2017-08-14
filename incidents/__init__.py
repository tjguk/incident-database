import os, sys
import datetime

from flask import Flask, redirect, render_template
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

    def __init__(self, one_liner, description, attachments=[], logged_on=None):
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

incident_pupils = db.Table(
    "incident_pupils",
    db.Column("incident_id", db.Integer, db.ForeignKey("incidents.id")),
    db.Column("pupil_id", db.Integer, db.ForeignKey("pupils.id"))
)

class Pupil(Model, db.Model):
    __tablename__ = "pupils"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True)
    incidents = db.relationship("Incident", secondary=incident_pupils, backref=db.backref("pupils"))

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
    return redirect("/incidents")

@app.route("/incidents", methods=["GET"])
def incidents():
    incidents = Incident.query.all()
    return render_template("incidents.html", title="Incidents", incidents=Incident.query.all())

@app.route("/incident/<incident_id>", methods=["GET"])
def show_incident(incident_id):
    incident = Incident.query.get(incident_id)
    return render_template("show_incident.html", title="Incident %s" % incident.identifier(), incident=incident)

#~ @app.route("/incidents/new", methods=["GET"])
#~ def new_incident():
    #~ return render_template("edit_incident.html")

#~ @app.route("/incidents", methods=["POST"])
#~ def create_incident():
    #~ raise NotImplementedError

#~ @app.route("/incident/<incident_id>", methods=["GET"])
#~ def show_incident(incident_id):
    #~ incident = Incident.query.get(incident_id)
    #~ return render_template("edit_incident", incident=incident)

#~ @app.route("/incident/<incident_id>/edit", methods=["GET"])
#~ def edit_incident(incident_id):
    #~ raise NotImplementedError

#~ @app.route("/incident/<incident_id>", methods=["POST", "PUT"])
#~ def update_incident(incident_id):
    #~ if request.method == "POST" and request.args.get("_method", "").upper() == "PUT":
        #~ request.method = "PUT"
    #~ else:
        #~ raise MethodNotAllowed(["PUT"])
    #~ raise NotImplementedError

#~ @app.route("/pupils", methods=["GET"])
#~ def pupils():
    #~ return "Pupils"

