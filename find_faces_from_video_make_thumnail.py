import face_recognition
import cv2
from PIL import Image, ImageFont, ImageDraw, ImageEnhance
#chitack
from os import listdir, mkdir, remove
from os.path import isdir, join, isfile, splitext, basename, exists, dirname
import datetime
from optparse import OptionParser
import glob

MAXSKIPCOUNT = 15
MAXCHECKLIFE = 4

def processremainframe(frames, outputfolder, videofile, found_count):
    count_found = 0
    for frame in frames:
        rgb_frame = frame[0][:, :, ::-1]

        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if len(face_encodings):
            print("Found %d from Queue (No.%d)" % (len(face_encodings), frame[1]))
            img_path = "%s/%s_frame%04d_who.jpg" % (outputfolder, basename(videofile).split(".")[0], frame[1])

            small_frame = cv2.resize(frame[0], (0, 0), fx=0.25, fy=0.25)
            cv2.imwrite(img_path, small_frame)
            count_found += 1
            found_count += 1
            if found_count >= MAXCHECKLIFE: break

    return count_found

def CheckVideo(videofile, outputfolder):
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
    #unit_per_frame = 51
    flag_count = 0
    found_count = 0
    skip_count = 0
    myq = []
    while True:
        # Grab a single frame of video
        ret, frame = input_movie.read()
        frame_number += 1
        # Quit when the input video file ends
        if not ret:
            break
        if flag_count or skip_count >= MAXSKIPCOUNT:
            skip_count = 0
        elif skip_count < MAXSKIPCOUNT:
            skip_count += 1
            if len(myq)>3: myq.pop(0)
            myq.append([frame, frame_number])
            continue
        print("Checking frame {} / {}".format(frame_number, length))

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_frame = frame[:, :, ::-1]

        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if len(face_encodings):
            print("Found %d" % len(face_encodings))
            img_path = "%s/%s_frame%04d_who.jpg" % (outputfolder, basename(videofile).split(".")[0], frame_number)

            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            cv2.imwrite(img_path, small_frame)

            found_count += 1
            if found_count >= MAXCHECKLIFE: break
            if len(myq):
                found_count += processremainframe(myq, outputfolder, videofile, found_count)
                myq = []
            if found_count >= MAXCHECKLIFE: break

    # All done!
    input_movie.release()
    cv2.destroyAllWindows()

def make_thumnail(source_folder, destination_folder):
    files = sorted(listdir(source_folder))

    final_image_width = 1920
    final_image_height = (int(len(files)/4) * 270)+270
    blank_image = Image.new('RGBA', (final_image_width, final_image_height), 'black')
    img_draw = ImageDraw.Draw(blank_image)
    index = 0
    previous_filename = ''
    font = ImageFont.truetype('NanumGothic.ttf', 80)
    sfont = ImageFont.truetype('NanumGothic.ttf', 10)
    for file in files:
        img = Image.open(join(source_folder, file))
        print(file)
        print("index:%d" % index)
        fna = file.split("_")[0]
        if index>0 and previous_filename != fna and (index%4)!=0:
            index = index + (4-(index%4))
        index += 1
        pindex = index-1
        previous_filename = file.split("_")[0]
        position = (pindex%4)*480, int(pindex/4) * 270
        print(position)
        blank_image.paste(img,position)
        img_draw.text(position, file, fill='blue', font=sfont)
        if (pindex % 4 ) == 0:
            position = (pindex % 4) * 480 + 30, int(pindex / 4) * 270 + 30
            img_draw.text(position, previous_filename, fill='yellow', font=font)
    blank_image.save("/%s/final.png" % (destination_folder))
    #blank_image.show()
    for file in files:
        remove(join(source_folder, file))


def get_faces_from_video(targetfolder, outputfolder):
    for item in listdir(targetfolder):
        #print(join(targetfolder, item))
        if isdir(join(targetfolder, item)):
            continue
        if item.upper().find(".MOV") >= 0:
            if not exists(outputfolder):
                mkdir(outputfolder, 755)
            start = datetime.datetime.now()
            print(start)
            CheckVideo(join(targetfolder, item), outputfolder)
            finish = datetime.datetime.now()
            print("Elapsed %s" % (finish - start))

if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("--source", dest="source",
                      help="specify folder of MOV files hat you want to detect a face.",
                      type='string',
                      default='/home/deeplearning/nasshare/chitack.chang/face/ipdisk/target0912')
    parser.add_option("--temporaryoutput", dest="temporaryoutput",
                      help="specify folder to make temporary image",
                      type='string',
                      default='/home/deeplearning/Desktop/face_recognition examples/output')

    (options, args) = parser.parse_args()

    get_faces_from_video(options.source, options.temporaryoutput)
    make_thumnail(options.temporaryoutput, options.source)
