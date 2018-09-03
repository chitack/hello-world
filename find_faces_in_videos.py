import face_recognition
import cv2
from os import listdir
from os.path import isdir, join, isfile, splitext, basename
import datetime


# This is a demo of running face recognition on a video file and saving the results to a new video file.
#
# PLEASE NOTE: This example requires OpenCV (the `cv2` library) to be installed only to read from your webcam.
# OpenCV is *not* required to use the face_recognition library. It's only required if you want to run this
# specific demo. If you have trouble installing it, try any of the other demos that don't require it instead.

def CheckVideo(videofile):
    print("check %s" % videofile)
    #return
    # Open the input movie file
    input_movie = cv2.VideoCapture(videofile)
    #input_movie.get(30)
    #input_movie = cv2.VideoCapture("hamilton_clip.mp4")
    length = int(input_movie.get(cv2.CAP_PROP_FRAME_COUNT))
    print("length:%d" % length)

    # Initialize some variables
    frame_number = 0
    unit_per_frame = length / 100
    while True:
        # Grab a single frame of video
        ret, frame = input_movie.read()
        frame_number += 1
        # Quit when the input video file ends
        if not ret:
            break
        #if frame_number & 0x1f : continue
        #if not frame_number % 15 == 0 : continue
        if not frame_number % unit_per_frame == 0: continue
        print("Checking frame {} / {}".format(frame_number, length))

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_frame = frame[:, :, ::-1]

        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if len(face_encodings):
            print("Found %d" % len(face_encodings))
            cv2.imwrite("output/%s_frame%d_who.jpg" % (basename(videofile), frame_number), frame)

    # All done!
    input_movie.release()
    cv2.destroyAllWindows()

#targetfolder = "/mnt/hgfs/shareforvm/"
targetfolder = "/home/deeplearning/nasshare/chitack.chang/face/ipdisk/target3/"

for item in listdir(targetfolder):
    #print(join(targetfolder, item))
    if isdir(join(targetfolder, item)):
        continue
    if item.upper().find(".MOV") >= 0:
        start = datetime.datetime.now()
        print(start)
        CheckVideo(join(targetfolder, item))
        finish = datetime.datetime.now()
        print("Elapsed %s" % (finish-start))
