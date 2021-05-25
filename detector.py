import cv2
import dlib
from tensorflow.keras import models
from tensorflow.keras.preprocessing import image
import os
import numpy as np


class Dfd:
    def detect(self,vpath):

        detector = dlib.get_frontal_face_detector()
        model = models.load_model('ml//model//selfds_idkif_itworked_mesocep_128_3.h5')

        #vid_fil = 'D://Projects//DeepfakesDetection//venv//ml//uploaded_videos'
        #vid_nam = 'v2attentioncheck.mp4'

        for fni in os.listdir('static/frames/'):
            os.remove(os.path.join('static/frames/', fni))

        cap = cv2.VideoCapture(vpath)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        frame_width = int(cap.get(3))
        frame_height = int(cap.get(4))
        size = (frame_width, frame_height)

        out = cv2.VideoWriter('static/marked/framed.mp4',
                              cv2.VideoWriter_fourcc(*'HEVC'),
                              20, size)
        wrt = []
        preds = []
        cl = []
        fr = []
        ver = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            fno = cap.get(cv2.CAP_PROP_POS_FRAMES)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector(gray)
            fi = 0
            fff = None
            for f in faces:
                x1 = max(f.left(), 0)
                y1 = max(f.top(), 0)
                x2 = max(f.right(), 0)
                y2 = max(f.bottom(), 0)
                ex = frame[y1:y2, x1:x2]
                fp = 'static/frames/' + str(fno) + '_' + str(fi) + '.jpg'  # FILEPATH
                wrt.append(cv2.imwrite('static/frames/' + str(fno) + '_' + str(fi) + '.jpg', ex))
        #imlist = [os.path.join('static/frames', f) for f in os.listdir('static/frames')]
        #for im in imlist:
                img = image.load_img(fp, target_size=(128, 128))
                fimg = image.img_to_array(img) / 255
                fnimg = np.expand_dims(fimg, 0)
                pr = model.predict(fnimg)[0, 0]
                preds.append(pr)
                if pr > 0.5:
                    cl.append("REAL")
                    fff = cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                else:
                    fr.append(str(fp[14:]))
                    cl.append("FAKE")
                    fff = cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            out.write(frame)

        #print("Found faces:", len(preds))
        fc = cl.count("FAKE")
        rc = cl.count("REAL")
        if fc > rc:
            ver.append("FAKE")
            acc = str((fc / (rc + fc)) * 100 - 5)
            acc = acc[:5]
            ver.append(acc)
            #print("FAKE video, Accuracy = {}".format((fc / (rc + fc)) * 100 - 12))
        else:
            ver.append("REAL")
            acc = str((rc / (rc + fc)) * 100 - 5)
            acc = acc[:5]
            ver.append(acc)
            #print("REAL video, Accuracy = {}".format((rc / (rc + fc)) * 100 - 12))
        #print(cl.count("REAL"), cl.count("FAKE"))
        return [cl,fr,ver]