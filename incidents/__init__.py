from flask import Flask, redirect
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

class Incident(Model, db.Model):
    __tablename__ = 'incidents'

    id = db.Column(db.Integer, primary_key=True)
    one_liner = db.Column(db.Text)
    description = db.Column(db.Text)
    action_taken = db.Column(db.Text)
    attachments = db.relationship("Attachment", backref="incident")

    def __init__(self, one_liner, description, attachments=[]):
        self.one_liner = one_liner
        self.description = description
        self.attachments = attachments

    def identifier(self):
        return "INC-%04d" % self.id

class Attachment(Model, db.Model):
    __tablename__ = "attachments"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.Text)
    incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id"))

    def __init__(self, filepath):
        self.filename = filepath

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
    return "Incidents"

@app.route("/incidents", methods=["POST"])
def create_incident():
    return "Incident created"

@app.route("/incident/<incident_id>", methods=["GET"])
def show_incident(incident_id):
    raise NotImplementedError

@app.route("/incident/<incident_id>/edit", methods=["GET"])
def edit_incident(incident_id=None):
    raise NotImplementedError

@app.route("/pupils", methods=["GET"])
def pupils():
    return "Pupils"

