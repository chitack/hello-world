from PIL import Image, ImageFont, ImageDraw, ImageEnhance
import face_recognition

#chitack
from os import listdir, mkdir
from os.path import isdir, join, isfile, splitext, basename, exists, dirname
import datetime

# to read full image from folder
source_folder = "/home/deeplearning/Desktop/face_recognition examples/output"
# to write face image folder.
destination_folder = "/home/deeplearning/nasshare/chitack.chang/face/candidate/"

def CheckImage(image_path):
    # Load the jpg file into a numpy array
    #image = face_recognition.load_image_file("IMG_2189.JPG")
    image = face_recognition.load_image_file(image_path)

    # Find all the faces in the image using the default HOG-based model.
    # This method is fairly accurate, but not as accurate as the CNN model and not GPU accelerated.
    # See also: find_faces_in_picture_cnn.py
    face_locations = face_recognition.face_locations(image)

    print("I found {} face(s) in this photograph.".format(len(face_locations)))

    index = 1
    for face_location in face_locations:

        # Print the location of each face in this image
        top, right, bottom, left = face_location
        print("A face is located at pixel location Top: {}, Left: {}, Bottom: {}, Right: {}".format(top, left, bottom, right))

        if 0:
            # You can access the actual face itself like this:
            face_image = image[top:bottom, left:right]
            pil_image = Image.fromarray(face_image)
            pil_image.show()

    source_img = Image.open(image_path).convert("RGBA")
    draw = ImageDraw.Draw(source_img)
    for face_location in face_locations:
        top, right, bottom, left = face_location
        draw.rectangle(((left, top), (right, bottom)), outline="yellow")
    #source_img.resize((480,270), Image.ANTIALIAS)
    source_img.resize((240, 135), Image.ANTIALIAS)
    source_img.show()


if 0:
    for item in listdir(source_folder):
        #print(join(targetfolder, item))
        if isdir(join(source_folder, item)):
            continue
        if item.upper().find(".JPG") >= 0 and item.upper().find("1146") >= 0:
            start = datetime.datetime.now()
            print(start)
            CheckImage(join(source_folder, item))
            finish = datetime.datetime.now()
            print("Elapsed %s" % (finish-start))

files = sorted(listdir(source_folder))
#print("%d" % len(files))

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
blank_image.save("/mnt/hgfs/shareforvm/face/final.png")
blank_image.show()
