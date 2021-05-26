from flask import Flask, escape, request, render_template, request, redirect, session, jsonify
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
import os
import json
import datetime
import detector
import video_info
import json
import random
import shutil
import ffmpeg

# d = detector.Dfd()
v = video_info.Video_info()

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

local_sv = params["local_server"]

app = Flask(__name__)
app.secret_key = 'ryan-secret-key'

# if (local_sv):
#     app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]
# else:
#     app.config['SQLALCHEMY_DATABASE_URI'] = params["prod_uri"]

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/dfdb'

# app.config["video_uploads"] = "D://Projects//DeepfakesDetection//venv//static//Uploaded_videos"

app.config["video_uploads"] = r"F:\Docs\Degree College ( St.Francis )\BE\B.E Proj\WebappPyc\static\Uploaded_videos"
app.config["api_uploads"] = r"F:\Docs\Degree College ( St.Francis )\BE\B.E Proj\WebappPyc\static\apiloc"
app.config["allowed_video_extensions"] = ["MP4", "MKV", "MOV", "WEBM", "FLV"]

db = SQLAlchemy(app)


# class Contact(db.Model):
#     sno = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(20), nullable=False)
#     email = db.Column(db.Integer, nullable=False)
#     message = db.Column(db.String(20), nullable=False)
#     date = db.Column(db.String(20), nullable=True)

class users(db.Model):
    __tablename__ = "users"
    uid = db.Column("UID", db.String(5), primary_key=True)
    uname = db.Column("username", db.String(25), nullable=False)
    password = db.Column("password", db.String(25), nullable=False)
    email = db.Column("email", db.String(25), nullable=False)
    DOB = db.Column("DOB", db.String(25), nullable=False)

    def __init__(self, uid, uname, password, email, DOB):
        self.uid = uid
        self.uname = uname
        self.password = password
        self.email = email
        self.DOB = DOB


# class Videos(db.Model):
#     vno = db.Column(db.Integer, primary_key=True)
#     vname = db.Column(db.String(25), nullable=False)
#     fakeframes = db.Column(db.Text, nullable=False)
#     vpath = db.Column(db.Text, nullable=False)
#     verd = db.Column(db.String(20), nullable=False)
#     vacc = db.Column(db.String(20), nullable=False)
#     vdate = db.Column(db.String(20), nullable=True)
#     vfrfake = db.Column(db.Integer, nullable=False)
#     vfrreal = db.Column(db.Integer, nullable=False)


class Video(db.Model):
    __tablename__ = "video"
    VID = db.Column("VID", db.String(5), primary_key=True)
    path = db.Column("path", db.String(200), nullable=False)
    doup = db.Column("doup", db.String(20), nullable=True)
    label = db.Column("label", db.String(5), nullable=False)
    fakeframes = db.Column("fakeframes", db.Text, nullable=True)
    vname = db.Column("vname", db.String(25), nullable=False)
    vfrfake = db.Column("vfrfake", db.Integer, nullable=False)
    vfrreal = db.Column("vfrreal", db.Integer, nullable=False)
    avgwt = db.Column("avgwt", db.String(25), nullable=True)
    UID = db.Column("UID", db.String(5), nullable=True)

    def __init__(self, VID, path, doup, label, fakeframes, vname, vfrfake, vfrreal, avgwt, UID):
        self.VID = VID
        self.path = path
        self.doup = doup
        self.label = label
        self.fakeframes = fakeframes
        self.vname = vname
        self.vfrfake = vfrfake
        self.vfrreal = vfrreal
        self.avgwt = avgwt
        self.UID = UID


# class


with open("config.json", "r") as c:
    params = json.load(c)["params"]


@app.route('/')
def indexpage():
    return render_template('index.html')


@app.route('/dbtest')
def testdb():
    # insdb()
    uans = users.query.all()
    # print(users.query.count())
    ass = " "
    for r in uans:
        ass += f"{r.uid} | {r.uname} | {r.password} | {r.email} | {r.DOB} \n"
    vans = Video.query.all()
    for v in vans:
        ass += f"{v.VID} | {v.path} | {v.doup} | {v.label} | {v.fakeframes} | {v.vname} | {v.vfrfake} | {v.vfrreal} | {v.avgwt} | {v.UID} | "
    return ass


def insdb():
    tot = users.query.count() + 1
    uid = 'U0000'
    uid = uid[:-1 * len(str(tot))] + str(tot)
    entry = users(uid, "josh", "adlkskd", "joah@email.com", datetime.datetime.now())
    db.session.add(entry)
    db.session.commit()


@app.route('/popular')
def popularpage():
    vid = Video.query.all()

    return render_template('popular.html', vid=vid)


@app.route('/detection')
def apipage():
    return render_template('api.html')


@app.route('/app')
def apppage():
    return render_template('app.html')


@app.route('/about')
def aboutpage():
    return render_template('about.html')


@app.route('/submit_form', methods=['get', 'post'])
def submit_form():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        msg = str(request.form.get('message'))

        # entry = Contact(name=name, email=email, message=msg, date=datetime.datetime.now())
        # db.session.add(entry)
        # db.session.commit()

    return render_template('about.html')


@app.route('/signup')
def signup():
    return render_template('about.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if ('user' in session and session['user'] == params['admin_user']):
        pass

    if request.method == 'POST':
        username = request.form.get('uname')
        password = request.form.get('pass')
        if (username == params['admin_usr'] and password == params["admin_pass"]):
            session['user'] = username
    return render_template('login.html')


def allowed_video(filename):  # check extension
    # Check if '.' exists in filename
    if not "." in filename:
        return False
    # Split the extension from the filename
    ext = filename.rsplit(".", 1)[1]
    # Check if the extension is in allowed_video_extensions
    if ext.upper() in app.config["allowed_video_extensions"]:
        return True
    else:
        return False


@app.route('/results')  # remove this
def results():
    # vid = Videos.query.order_by(Videos.vno.desc()).first()
    vidres = {}
    if "vidresd" in session:
        vidres = session["vidresd"]

    vid_list = []
    meta = []
    # vid_list.append(vid.vname)
    vid_list.append(vidres["vname"])

    # fkfrmj = json.loads(vid.fakeframes)
    fkfrmj = json.loads(vidres["fakeframes"])

    if len(fkfrmj) > 15:
        fkfrm = random.sample(fkfrmj, 15)
    else:
        fkfrm = fkfrmj

    vid_list.append(fkfrm)
    # vid_list.append(vid.vpath)
    # vid_list.append(vid.vdate)
    # vid_list.append(vid.vfrfake)
    # vid_list.append(vid.vfrreal)
    # vid_list.append(vid.verd)
    # vid_list.append(vid.vacc)

    vid_list.append(vidres["vpath"])
    vid_list.append(vidres["doup"])
    vid_list.append(vidres["vfrfake"])
    vid_list.append(vidres["vfrreal"])
    vid_list.append(vidres["label"])
    acc = str(vidres["avgwt"] * 100)[:6]
    vid_list.append(acc)
    print("res:", vidres["vpath"])

    probe = ffmpeg.probe(vidres["vpath"])
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    meta.append(int(video_stream['width']))
    meta.append(int(video_stream['height']))
    meta.append(str(video_stream['codec_name']))
    meta.append(int(video_stream['bit_rate']))
    meta.append(str(video_stream['duration']))
    meta.append(str(video_stream['avg_frame_rate'])[:2])

    return render_template("results.html", vid_list=vid_list, meta=meta)


@app.route("/upload-video", methods=["GET", "POST"])
def upload_video():
    if request.method == "POST":
        video = request.files["video"]
        if video.filename == "":  # check filename exists
            print("No filename")
            return redirect(request.url)
        if allowed_video(video.filename):  # check for extension
            # folder = r'D:\Projects\DeepfakesDetection\venv\static\frames'
            folder = r"F:\Docs\Degree College ( St.Francis )\BE\B.E Proj\WebappPyc\static\frames"
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
            filename = secure_filename(video.filename)
            video.save(os.path.join(app.config["video_uploads"], filename))  # save video
            vpath = os.path.join(app.config["video_uploads"], filename)
            print("up vpath", vpath)
            dfdobj = detector.Dfd(vpath)
            va = dfdobj.detect()
            fkr = va[1]
            fkrs = json.dumps(fkr)

            vidresd = {"vname": filename, "vpath": vpath, "doup": datetime.datetime.now(),
                       "label": "REAL" if va[2] == 1 else "FAKE", "fakeframes": fkrs, "vfrfake": va[0].count(0),
                       "vfrreal": va[0].count(1), "avgwt": va[3], "UID": None}

            # entry = Videos(vname=filename, fakeframes=fkrs, vpath=vpath, verd=va[2][0], vacc=va[2][1],
            #                vdate=datetime.datetime.now(), vfrfake=va[0].count("FAKE"), vfrreal=va[0].count("REAL"))
            # db.session.add(entry)
            # db.session.commit()
            session['vidresd'] = vidresd
            return redirect(request.url)
        else:
            print("That file extension is not allowed")
            return redirect(request.url)
    return results()


@app.route('/dfdapi/<usrname>', methods=["POST", "GET"])
def apires(usrname):
    msgd = {}
    if request.method == "POST":
        video = request.files["file"]
        if video.filename == "":  # check filename exists
            msgd["ERROR"] = "FileNameNotFound"
            return jsonify(msgd)
        elif not allowed_video(video.filename):
            msgd["ERROR"] = "VideoFormatUnacceptable"
            return jsonify(msgd)

        folder = r"F:\Docs\Degree College ( St.Francis )\BE\B.E Proj\WebappPyc\static\frames"
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))

        vname = video.filename
        if vname in os.listdir(app.config["api_uploads"]):
            if os.path.isfile(os.path.join(app.config["api_uploads"], vname)):
                os.remove(os.path.join(app.config["api_uploads"], vname))

        filename = secure_filename(vname)
        video.save(os.path.join(app.config["api_uploads"], filename))
        vpath = os.path.join(app.config["api_uploads"], filename)

        dfdobj = detector.Dfd(vpath)
        va = dfdobj.detect()
        fkr = va[1]
        fkrs = [s.split('/')[-1][:-4] for s in fkr]
        # fkrs = json.dumps(fkr)

        vidresd = {"videoname": filename, "date_of_upload": datetime.datetime.now(),
                   "label": "REAL" if va[2] == 1 else "FAKE", "fakeframes": fkrs, "fake_frame_count": va[0].count(0),
                   "real_frame_count": va[0].count(1), "Accuracy": va[3], "UID": str(usrname)}
        return jsonify(vidresd)

    else:
        return "Please send POST request"


app.run(debug=True)
