import face_recognition
import cv2
from PIL import Image, ImageFont, ImageDraw, ImageEnhance
#chitack
from os import listdir, mkdir, remove
from os.path import isdir, join, isfile, splitext, basename, exists, dirname
import datetime
from optparse import OptionParser

import sys
import glob

MAXSKIPCOUNT = 15
MAXCHECKLIFE = 2

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

def processremainframe(frames, outputfolder, videofile):
    count_found = 0
    for frame in frames:
        print(outputfolder, basename(videofile), frame[1])
        img_path = "%s/%s_frame%04d_who.jpg" % (outputfolder, basename(videofile).split(".")[0], frame[1])

        try:
            height, width, channels = frame[0].shape
            iih = (int)(height/4)
            iiw = (int)(width/4)
            small_frame = cv2.resize(frame[0][iih:3*iih,iiw:iiw*3], (THUMB_WIDTH, THUMB_HEIGHT))
            cv2.imwrite(img_path, small_frame)
        except Exception as e:
            print('Error on line{}'.format(sys.exe_info()[-1].tb_lineno), type(e).__name__, e)
            small_frame = cv2.resize(frame[0], (THUMB_WIDTH, THUMB_HEIGHT))
            cv2.imwrite(img_path, small_frame)
        count_found += 1
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
    found_count = 0
    myq = []

    uu = int(length/(10*MAXCHECKLIFE))
    mc = []
    for i in range(0,MAXCHECKLIFE):
        mc.append(uu*i)
    print(mc)

    while frame_number <= (MAXCHECKLIFE*uu+1):
        ret, frame = input_movie.read()
        if not ret:
            break
        if frame_number in mc:
            myq.append([frame,frame_number])
        frame_number += 1
        if len(myq) >= MAXCHECKLIFE:
            break

    if found_count < MAXCHECKLIFE:
        processremainframe(myq, outputfolder, videofile)
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
        remove(join(source_folder, file))
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
                      default='/home/deeplearning/nasshare/chitack.chang/face/ipdisk/target0108')
    parser.add_option("--temporaryoutput", dest="temporaryoutput",
                      help="specify folder to make temporary image\n[default:%default]",
                      type='string',
                      default='/home/deeplearning/Desktop/face_recognition examples/output')

    (options, args) = parser.parse_args()

    start = datetime.datetime.now()
    if not exists(join(options.source, 'final.png')):
        get_faces_from_video(options.source, options.temporaryoutput)
        make_thumnail(options.temporaryoutput, options.source)
    else:
        print("There is already final.png. It looks like it has been done (%s)" % options.source)
    print("Total Elapsed:%s" %(datetime.datetime.now() - start))