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

THUMB_WIDTH = 240
THUMB_HEIGHT = 135
COUNT_OF_LINE_IN_THUMB = (MAXCHECKLIFE)

def getCenterImage(face_location, frame):
    top, right, bottom, left = face_location
    center_x = left + int((right - left) / 2)
    center_y = top + int((bottom - top) / 2)
    if (center_x - int(THUMB_WIDTH / 2)) < 0:
        tleft = 0
    else:
        tleft = center_x - int(THUMB_WIDTH / 2)
    tright = tleft + THUMB_WIDTH

    if (center_y - int(THUMB_HEIGHT / 2)) < 0:
        ttop = 0
    else:
        ttop = center_y - int(THUMB_HEIGHT / 2)
    tbottom = ttop + THUMB_HEIGHT

    rgb_frame = frame[:, :, ::-1]
    face_image = rgb_frame[ttop:tbottom, tleft:tright]
    #print(face_location)
    #print(ttop, tright, tbottom, tleft)
    return face_image

def processremainframe(frames, outputfolder, videofile, found_count, force_flag):
    count_found = 0
    for frame in frames:
        rgb_frame = frame[0][:, :, ::-1]

        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if force_flag and len(face_locations) < 1:
            print("@@Force Found %d from Queue (No.%d)" % (len(face_encodings), frame[1]))
            img_path = "%s/%s_frame%04d_who.jpg" % (outputfolder, basename(videofile).split(".")[0], frame[1])

            #small_frame = cv2.resize(frame[0], (0, 0), fx=0.25, fy=0.25)
            small_frame = cv2.resize(frame[0], (THUMB_WIDTH, THUMB_HEIGHT))
            cv2.imwrite(img_path, small_frame)
            count_found += 1
            found_count += 1
            if found_count >= MAXCHECKLIFE: break

        for face_location in face_locations:
            face_image = getCenterImage(face_location, frame[0])
            pil_image = Image.fromarray(face_image)

            print("@@Found %d from Queue (No.%d)" % (len(face_encodings), frame[1]))
            img_path = "%s/%s_frame%04d_who.jpg" % (outputfolder, basename(videofile).split(".")[0], frame[1])

            pil_image.save(img_path)
            count_found += 1
            found_count += 1
            if found_count >= MAXCHECKLIFE: break
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
    t_start = datetime.datetime.now()
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
            if len(myq)>(COUNT_OF_LINE_IN_THUMB): myq.pop(0)
            myq.append([frame, frame_number])
            continue
        # break if it takes 10 seconds.
        if ( datetime.timedelta(seconds=10) < (datetime.datetime.now() - t_start)):
            print("Time out! (%d)" % (len(myq)))
            break

        print("Checking frame {} / {}".format(frame_number, length))

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_frame = frame[:, :, ::-1]

        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if 0 and len(face_encodings):
            print("Found %d" % len(face_encodings))
            img_path = "%s/%s_frame%04d_who.jpg" % (outputfolder, basename(videofile).split(".")[0], frame_number)

            #small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            small_frame = cv2.resize(frame, (THUMB_WIDTH, THUMB_HEIGHT))
            cv2.imwrite(img_path, small_frame)

            found_count += 1
            if found_count >= MAXCHECKLIFE: break
            if len(myq):
                found_count += processremainframe(myq, outputfolder, videofile, found_count, False)
                #myq = []
            if found_count >= MAXCHECKLIFE: break

        for face_location in face_locations:
            print("Found %d" % len(face_encodings))
            img_path = "%s/%s_frame%04d_who.jpg" % (outputfolder, basename(videofile).split(".")[0], frame_number)

            face_image = getCenterImage(face_location, frame)
            pil_image = Image.fromarray(face_image)
            pil_image.save(img_path)
            found_count += 1
            if found_count >= MAXCHECKLIFE: break
            if len(myq):
                found_count += processremainframe(myq, outputfolder, videofile, found_count,False)
                myq = []
            if found_count >= MAXCHECKLIFE: break
        if found_count >= MAXCHECKLIFE: break

    if found_count < MAXCHECKLIFE:
        processremainframe(myq, outputfolder, videofile, found_count,True)
    # All done!
    input_movie.release()
    cv2.destroyAllWindows()

def make_thumnail(source_folder, destination_folder):
    files = sorted(listdir(source_folder))

    final_image_width = THUMB_WIDTH * COUNT_OF_LINE_IN_THUMB
    final_image_height = (int(len(files)/COUNT_OF_LINE_IN_THUMB) * THUMB_HEIGHT)+THUMB_HEIGHT
    blank_image = Image.new('RGBA', (final_image_width, final_image_height), 'black')
    img_draw = ImageDraw.Draw(blank_image)
    index = 0
    previous_filename = ''
    fsize = 40
    font = ImageFont.truetype('NanumGothic.ttf', fsize)
    sfont = ImageFont.truetype('NanumGothic.ttf', 5)
    for file in files:
        img = Image.open(join(source_folder, file))
        print(file)
        print("index:%d" % index)
        fna = file.split("_")[0]
        if index>0 and previous_filename != fna and (index%COUNT_OF_LINE_IN_THUMB)!=0:
            index = index + (COUNT_OF_LINE_IN_THUMB-(index%COUNT_OF_LINE_IN_THUMB))
        index += 1
        pindex = index-1
        previous_filename = file.split("_")[0]
        position = (pindex%COUNT_OF_LINE_IN_THUMB)*THUMB_WIDTH, int(pindex/COUNT_OF_LINE_IN_THUMB) * THUMB_HEIGHT
        print(position)
        blank_image.paste(img,position)
        img_draw.text(position, file, fill='blue', font=sfont)

    #blank_image.show()
    index = 0
    previous_filename = ''
    for file in files:
        #remove(join(source_folder, file))
        fna = file.split("_")[0]
        if index > 0 and previous_filename != fna and (index % COUNT_OF_LINE_IN_THUMB) != 0:
            index = index + (COUNT_OF_LINE_IN_THUMB - (index % COUNT_OF_LINE_IN_THUMB))
        index += 1
        pindex = index - 1
        previous_filename = file.split("_")[0]
        if (pindex % COUNT_OF_LINE_IN_THUMB ) == 0:
            #position = (pindex % COUNT_OF_LINE_IN_THUMB) * THUMB_WIDTH + 30, int(pindex / COUNT_OF_LINE_IN_THUMB) * THUMB_HEIGHT + 30
            position = (pindex % COUNT_OF_LINE_IN_THUMB) * THUMB_WIDTH + 30, int(pindex / COUNT_OF_LINE_IN_THUMB) * THUMB_HEIGHT + THUMB_HEIGHT - fsize - 10
            img_draw.text(position, previous_filename, fill='white', font=font)
            img_draw.line( ((0, int(pindex / COUNT_OF_LINE_IN_THUMB)* THUMB_HEIGHT+THUMB_HEIGHT), (final_image_width, int(pindex / COUNT_OF_LINE_IN_THUMB)* THUMB_HEIGHT+ THUMB_HEIGHT)), fill="white", width=3)
            #img_draw.rectangle(((0, int(pindex / COUNT_OF_LINE_IN_THUMB)* THUMB_HEIGHT), (final_image_width, int(pindex / COUNT_OF_LINE_IN_THUMB)* THUMB_HEIGHT+ THUMB_HEIGHT)), outline="white")
        pass

    blank_image.save("/%s/final.png" % (destination_folder))

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
                      help="specify folder of MOV files hat you want to detect a face.\n[default:%default]",
                      type='string',
                      default='/home/deeplearning/nasshare/chitack.chang/face/ipdisk/target0912')
    parser.add_option("--temporaryoutput", dest="temporaryoutput",
                      help="specify folder to make temporary image\n[default:%default]",
                      type='string',
                      default='/home/deeplearning/Desktop/face_recognition examples/output')

    (options, args) = parser.parse_args()

    if not exists(join(options.source, 'final.png')):
        get_faces_from_video(options.source, options.temporaryoutput)
        make_thumnail(options.temporaryoutput, options.source)
    else:
        print("There is already final.png. It looks like it has been done (%s)" % options.source)
