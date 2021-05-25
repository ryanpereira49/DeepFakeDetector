import cv2
import dlib
from tensorflow.keras import models
from tensorflow.keras.preprocessing import image
import os
import numpy as np

detector = dlib.get_frontal_face_detector()


class FrameLabel():

    def __init__(self, fno, ltrb, lb):
        self.fno = fno

        self.ltrb = ltrb
        self.x1 = ltrb[0]
        self.y1 = ltrb[1]
        self.x2 = ltrb[2]
        self.y2 = ltrb[3]

        self.lb = lb
        self.colr = (0, 255, 0) if lb == 1 else (0, 0, 255)

    def drawBox(self, imgfr):
        fff = cv2.rectangle(imgfr, (self.x1, self.y1), (self.x2, self.y2), self.colr, 2)
        return fff

    def coords(self):
        return f"x1 {self.x1}, y1 {self.y1}, x2 {self.x2}, y2 {self.y2}"


class Dfd():

    def __init__(self, vpath):
        self.vpath = vpath
        self.model = models.load_model('ml//model//selfds_idkif_itworked_mesocep_128_3.h5')
        self.frameMark = {}
        for fni in os.listdir('static/frames/'):
            os.remove(os.path.join('static/frames/', fni))

    def classify(self, cls):
        fks = []
        rls = []
        prev = cls[0]
        ccount = 0

        for cli in cls:
            if prev == cli:
                ccount += 1
            else:
                if prev == 1:
                    rls.append(ccount)
                else:
                    fks.append(ccount)
                ccount = 1
            prev = cli
        else:
            if prev == 1:
                rls.append(ccount)
            else:
                fks.append(ccount)

        return fks, rls

    def makepreds(self):
        cap = cv2.VideoCapture(self.vpath)
        print("Frame count:", cap.get(cv2.CAP_PROP_FRAME_COUNT))

        frame_width = int(cap.get(3))
        frame_height = int(cap.get(4))
        size = (frame_width, frame_height)

        wrt = []
        preds = []
        cl = []
        fr = []

        while True:
            fno = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector(gray)
            fi = 0
            fff = None

            if len(faces) == 0:
                self.frameMark[fno] = 0
                continue

            for f in faces:
                x1 = max(f.left(), 0)
                y1 = max(f.top(), 0)
                x2 = max(f.right(), 0)
                y2 = max(f.bottom(), 0)
                ex = frame[y1:y2, x1:x2]

                # SAVE FACE in temp folder
                fp = 'static/frames/' + str(fno) + '_' + str(fi) + '.jpg'  # FILEPATH
                wrt.append(cv2.imwrite(fp, ex))
                fi += 1

                # PREDICTION
                img = image.load_img(fp, target_size=(128, 128))
                fimg = image.img_to_array(img) / 255
                fnimg = np.expand_dims(fimg, 0)
                pr = self.model.predict(fnimg)[0, 0]

                preds.append(pr)
                if pr > 0.5:
                    cl.append(1)
                    self.frameMark[fno] = FrameLabel(fno, [x1, y1, x2, y2], 1)
                else:
                    cl.append(0)
                    fr.append(fp)
                    self.frameMark[fno] = FrameLabel(fno, [x1, y1, x2, y2], 0)

        print("All write:{}".format(all(wrt)))
        return preds, cl, fr

    def markit(self, verdict):
        border = (0, 255, 0) if verdict == 1 else (0, 0, 255)

        cap = cv2.VideoCapture(self.vpath)
        # print("Frame count:", cap.get(cv2.CAP_PROP_FRAME_COUNT))

        frame_width = int(cap.get(3)) + 8
        frame_height = int(cap.get(4)) + 8
        size = (frame_width, frame_height)

        out = cv2.VideoWriter('static/marked/framed.mp4',
                              cv2.VideoWriter_fourcc(*'HEVC'),
                              20, size)

        while True:
            fno = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            ret, frame = cap.read()

            if not ret:
                break

            fff = None
            frlobj = self.frameMark[fno]

            if frlobj != 0:
                fff = frlobj.drawBox(frame)
            else:
                fff = frame

            bordersize = 4
            fff = cv2.copyMakeBorder(
                fff,
                top=bordersize,
                bottom=bordersize,
                left=bordersize,
                right=bordersize,
                borderType=cv2.BORDER_CONSTANT,
                value=border
            )

            label = "REAL" if verdict == 1 else "DEEPFAKE"
            FONT = cv2.FONT_HERSHEY_SIMPLEX
            FONT_SCALE = 0.8
            FONT_THICKNESS = 2
            bg_color = (0, 255, 0) if verdict == 1 else (0, 0, 255)
            label_color = (255, 255, 255)

            (label_width, label_height), baseline = cv2.getTextSize(label, FONT, FONT_SCALE, FONT_THICKNESS)
            label_height += 14
            dx = frame_height - label_height + baseline
            dy = frame_width - label_width

            fff[dx:frame_width, 0:label_width] = bg_color
            fff = cv2.putText(fff, label, (0, frame_height), FONT, FONT_SCALE, label_color, FONT_THICKNESS)
            out.write(fff)

    def detect(self):
        preds, cl, fr = self.makepreds()
        fksq, rlsq = self.classify(cl)
        fc = cl.count(0)
        rc = cl.count(1)
        avgwt = sum(preds) / len(preds)

        mxfsq = 0
        mxrsq = 0

        if fksq:
            mxfsq = max(fksq)

        if rlsq:
            mxrlq = max(rlsq)

        # print(vidname)
        # print(f"fake {fc}, real {rc}")
        # print("Avg weights:{}".format(avgwt))
        # print("Found faces:", len(preds))
        # print("Fake seq:{}, Real seq:{}".format(mxfsq, mxrlq))

        verdict = 1 if mxrsq > mxfsq else 0
        self.markit(verdict)

        return [cl, fr, verdict, avgwt]

# dfdobj = Dfd(vidname)
# ress = dfdobj.detect()
# print(ress[1])
