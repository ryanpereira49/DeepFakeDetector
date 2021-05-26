from flask import Flask, escape, request, render_template, request, redirect, session, url_for, jsonify
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

d = detector.Dfd()
v = video_info.Video_info()

with open('config.json','r') as c:
    params = json.load(c)["params"]

local_sv = params["local_server"]

app = Flask(__name__)
app.secret_key = 'ryan-secret-key'


if(local_sv):
    app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["prod_uri"]

app.config["video_uploads"] = "D://Projects//DeepfakesDetection//venv//static//Uploaded_videos"
app.config["allowed_video_extensions"] = ["MP4", "MKV", "MOV", "WEBM","FLV"]

db = SQLAlchemy(app)


class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.Integer, nullable=False)
    message = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(20), nullable=True)

class Videos(db.Model):
    vno = db.Column(db.Integer, primary_key=True)
    vname = db.Column(db.String(25), nullable=False)
    fakeframes = db.Column(db.Text, nullable=False)
    vpath = db.Column(db.Text, nullable=False)
    verd = db.Column(db.String(20), nullable=False)
    vacc = db.Column(db.String(20), nullable=False)
    vdate = db.Column(db.String(20), nullable=True)
    vfrfake = db.Column(db.Integer, nullable=False)
    vfrreal = db.Column(db.Integer, nullable=False)
    vUname = db.Column(db.String(20), nullable=True)

class Users(db.Model):
    Uno = db.Column(db.Integer, primary_key=True)
    Uname = db.Column(db.String(20), nullable=False)
    Uemail = db.Column(db.String(20), nullable=False)
    Upass = db.Column(db.String(20), nullable=False)

#class



with open("config.json","r") as c:
    params = json.load(c)["params"]

@app.route('/')
def indexpage():
    return render_template('index.html')

@app.route('/popular')
def popularpage():
    vid = Videos.query.all()

    return render_template('popular.html',vid=vid)

@app.route('/detection')
def apipage():
    return render_template('api.html')

@app.route('/app')
def apppage():
    return render_template('app.html')

@app.route('/about')
def aboutpage():
    return render_template('about.html')

@app.route('/submit_form',methods=['get','post'])
def submit_form():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        msg = str(request.form.get('message'))

        entry = Contact(name=name,email=email,message=msg,date=datetime.datetime.now())
        db.session.add(entry)
        db.session.commit()

    return render_template('about.html')

@app.route('/signup',methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        usersdb = Users.query.all()
        Unamef = request.form.get('uname')
        Uemailf = request.form.get('uemail')
        Upassf = request.form.get('upass')
        for u in usersdb:
            if Unamef == u.Uname:
                return render_template('signup.html',msg='Username Alerady Exists')
            if Uemailf == u.Uemail:
                return render_template('signup.html',msg='Email Alerady Exists')
        entry = Users(Uname=Unamef,Uemail=Uemailf,Upass=Upassf)
        db.session.add(entry)
        db.session.commit()
        return render_template('login.html',msg='Registration Sucessful, You can now Login')
    return render_template('signup.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if('user' in session and session['user'] == params['admin_user']):
        pass
    
    if request.method == 'POST':
        usersdb = Users.query.all()
        Unamef = request.form.get('uname')
        Upassf = request.form.get('upass')
        x = [u for u in usersdb if Unamef == u.Uname and Upassf == u.Upass]
        if not x:
            return render_template('login.html',msg="Invalid Credentials!")
        if x[0].Uname == Unamef:
            session['Uname'] = Unamef
            session['login'] = True
            return render_template('index.html')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('Uname',None)
    return render_template('login.html')

def allowed_video(filename): #check extension
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

@app.route('/results') #remove this
def results():

    vid = Videos.query.order_by(Videos.vno.desc()).first()

    vid_list = []
    meta = []
    vid_list.append(vid.vname)
    fkfrmj = json.loads(vid.fakeframes)
    if len(fkfrmj) > 15:
        fkfrm = random.sample(fkfrmj,15)
    else:
        fkfrm = fkfrmj
    vid_list.append(fkfrm)
    vid_list.append(vid.vpath)
    vid_list.append(vid.vdate)
    vid_list.append(vid.vfrfake)
    vid_list.append(vid.vfrreal)
    vid_list.append(vid.verd)
    vid_list.append(vid.vacc)

    probe = ffmpeg.probe(vid.vpath)
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    meta.append(int(video_stream['width']))
    meta.append(int(video_stream['height']))
    meta.append(str(video_stream['codec_name']))
    meta.append(int(video_stream['bit_rate']))
    meta.append(str(video_stream['duration']))
    meta.append(str(video_stream['avg_frame_rate'])[:2])

    return render_template("results.html",vid_list=vid_list,meta=meta)


@app.route("/upload-video", methods=["GET", "POST"])
def upload_video():
    cnt9 = 1
    if request.method == "POST":
            video = request.files["video"]
            if video.filename == "": #check filename exists
                print("No filename")
                return redirect(request.url)
            if allowed_video(video.filename): #check for extension
                folder = r'D:\Projects\DeepfakesDetection\venv\static\frames'
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
                for root, dirs, files in os.walk(app.config["video_uploads"]):
                    for filenamez in files:
                        if filenamez.endswith(('.MP4','.MKV','.MOV','.WEBM','.FLV','.mp4','mkv','.mov','.webm','.flv')):
                            cnt9 += 1
                nfilename = filename[:-4]
                ext = filename[-4:]
                filename = nfilename+str(cnt9)+ext
                video.save(os.path.join(app.config["video_uploads"], filename)) #save video
                vpath = os.path.join(app.config["video_uploads"], filename)
                va = d.detect(vpath,filename)
                #v.vid(va[0],vpath)
                fkr = va[1]
                fkrs = json.dumps(fkr)
                try:
                    UnameVn = session['Uname']
                except:
                    UnameVn = "Guest"
                entry = Videos(vname=filename, fakeframes=fkrs, vpath=vpath,verd=va[2][0],vacc=va[2][1], vdate=datetime.datetime.now(),vfrfake=va[0].count("FAKE"),vfrreal=va[0].count("REAL"),vUname=UnameVn)
                db.session.add(entry)
                db.session.commit()
                return redirect(request.url)
            else:
                print("That file extension is not allowed")
                return redirect(request.url)
    return results()

@app.route('/dfapi', methods=["POST"])
def dfapi():
    # check if the post request has the file part
    if 'video' not in request.files:
        resp = jsonify({'message': 'No video part in the request'})
        resp.status_code = 400
        return resp
    video = request.files["video"]
    if video.filename == "":  # check filename exists
        resp = jsonify({'message': 'No file selected for uploading'})
        resp.status_code = 400
        return resp
    if video and allowed_video(video.filename):

        folder = r'D:\Projects\DeepfakesDetection\venv\static\frames'
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
        cnt9 = 1
        for root, dirs, files in os.walk(app.config["video_uploads"]):
            for filenamez in files:
                if filenamez.endswith(('.MP4', '.MKV', '.MOV', '.WEBM', '.FLV', '.mp4', 'mkv', '.mov', '.webm', '.flv')):
                    cnt9 += 1
        nfilename = filename[:-4]
        ext = filename[-4:]
        filename = nfilename + str(cnt9) + ext
        video.save(os.path.join(app.config["video_uploads"], filename))  # save video
        vpath = os.path.join(app.config["video_uploads"], filename)
        va = d.detect(vpath, filename)
        # v.vid(va[0],vpath)
        fkr = va[1]
        fkrs = json.dumps(fkr)
        try:
            UnameVn = session['Uname']
        except:
            UnameVn = "Guest"
        entry = Videos(vname=filename, fakeframes=fkrs, vpath=vpath, verd=va[2][0], vacc=va[2][1],
                       vdate=datetime.datetime.now(), vfrfake=va[0].count("FAKE"), vfrreal=va[0].count("REAL"),
                       vUname=UnameVn)
        db.session.add(entry)
        db.session.commit()
        ret = api_result()
        resp = jsonify(ret)
        resp.status_code = 201
        return resp
    else:
        resp = jsonify({'message': 'Allowed file types are .MP4 .MKV .MOV .WEBM .FLV'})
        resp.status_code = 400
        return res

def api_result():

    vid = Videos.query.order_by(Videos.vno.desc()).first()

    vid_list = []
    meta = []
    vid_dict = {
        "name" : vid.vname,
        "url" : vid.vpath,
        "date" : vid.vdate,
        "fake_frames" : vid.vfrfake,
        "real_frames" : vid.vfrreal,
        "verdict" : vid.verd,
        "accuracy" : vid.vacc
    }

    probe = ffmpeg.probe(vid.vpath)
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)

    meta_dict = {
        "width": int(video_stream['width']),
        "height" : int(video_stream['height']),
        "codec_name" : str(video_stream['codec_name']),
        "bit_rate" : int(video_stream['bit_rate']),
        "duration" : str(video_stream['duration']),
        "avg_frame_rate": str(video_stream['avg_frame_rate'])[:2]

    }

    return [vid_dict,meta_dict]

@app.route('/dfapi/data')
def dfapi_data():
    vid_list = []
    v = Videos.query.all()
    for vid in v:
        vid_dict = {
            "name": vid.vname,
            "url": vid.vpath,
            "date": vid.vdate,
            "fake_frames": vid.vfrfake,
            "real_frames": vid.vfrreal,
            "verdict": vid.verd,
            "accuracy": vid.vacc
        }
        vid_list.append(vid_dict)
    resp = jsonify(vid_list)
    resp.status_code = 201
    return resp


app.run(debug=True)