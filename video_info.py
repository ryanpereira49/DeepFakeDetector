import ffmpeg
import math

class Video_info:
    def vid(self,cl,vpath):
        vid_inf = []
        real_cnt = cl.count("REAL")
        fake_cnt = cl.count("FAKE")
        total_frames = real_cnt + fake_cnt
        accuracy = fake_cnt/total_frames * 100
        vid_inf.append(accuracy)

        probe = ffmpeg.probe(args.in_filename)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        width = int(video_stream['width'])
        vid_inf.append(width)
        height = int(video_stream['height'])
        vid_inf.append(height)


        return
