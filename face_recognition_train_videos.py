"""
This is an example of using the k-nearest-neighbors(knn) algorithm for face recognition.

When should I use this example?
This example is useful when you whish to recognize a large set of known people,
and make a prediction for an unkown person in a feasible computation time.

Algorithm Description:
The knn classifier is first trained on a set of labeled(known) faces, and can then predict the person
in an unkown image by finding the k most similar faces(images with closet face-features under eucledian distance) in its training set,
and performing a majority vote(possibly weighted) on their label.
For example, if k=3, and the three closest face images to the given image in the training set are one image of Biden and two images of Obama,
The result would be 'Obama'.
*This implemententation uses a weighted vote, such that the votes of closer-neighbors are weighted more heavily.

Usage:
-First, prepare a set of images of the known people you want to recognize.
 Organize the images in a single directory with a sub-directory for each known person.
-Then, call the 'train' function with the appropriate parameters.
 make sure to pass in the 'model_save_path' if you want to re-use the model without having to re-train it.
-After training the model, you can call 'predict' to recognize the person in an unknown image.

NOTE: This example requires scikit-learn to be installed! You can install it with pip:
$ pip3 install scikit-learn
"""

from math import sqrt
from sklearn import neighbors
from os import listdir, mkdir
from os.path import isdir, join, isfile, splitext, basename, dirname, exists
import pickle
from PIL import Image, ImageFont, ImageDraw, ImageEnhance
import face_recognition
from face_recognition import face_locations
from face_recognition.cli import image_files_in_folder
import datetime
import cv2
from optparse import OptionParser
import glob

MAXSKIPCOUNT = 15
MAXCHECKLIFE = 5


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def train(train_dir, model_save_path = "", n_neighbors = None, knn_algo = 'ball_tree', verbose=False):
    """
    Trains a k-nearest neighbors classifier for face recognition.

    :param train_dir: directory that contains a sub-directory for each known person, with its name.

     (View in source code to see train_dir example tree structure)

     Structure:
        <train_dir>/
        ├── <person1>/
        │   ├── <somename1>.jpeg
        │   ├── <somename2>.jpeg
        │   ├── ...
        ├── <person2>/
        │   ├── <somename1>.jpeg
        │   └── <somename2>.jpeg
        └── ...
    :param model_save_path: (optional) path to save model of disk
    :param n_neighbors: (optional) number of neighbors to weigh in classification. Chosen automatically if not specified.
    :param knn_algo: (optional) underlying data structure to support knn.default is ball_tree
    :param verbose: verbosity of training
    :return: returns knn classifier that was trained on the given data.
    """
    X = []
    y = []
    for class_dir in listdir(train_dir):
        if not isdir(join(train_dir, class_dir)):
            continue
        for img_path in image_files_in_folder(join(train_dir, class_dir)):
            image = face_recognition.load_image_file(img_path)
            faces_bboxes = face_locations(image)
            if len(faces_bboxes) != 1:
                if verbose:
                    print("image {} not fit for training: {}".format(img_path, "didn't find a face" if len(faces_bboxes) < 1 else "found more than one face"))
                continue
            X.append(face_recognition.face_encodings(image, known_face_locations=faces_bboxes)[0])
            y.append(class_dir)


    if n_neighbors is None:
        n_neighbors = int(round(sqrt(len(X))))
        if verbose:
            print("Chose n_neighbors automatically as:", n_neighbors)

    knn_clf = neighbors.KNeighborsClassifier(n_neighbors=n_neighbors, algorithm=knn_algo, weights='distance')
    knn_clf.fit(X, y)

    if model_save_path != "":
        with open(model_save_path, 'wb') as f:
            pickle.dump(knn_clf, f)
    return knn_clf

def predict(X_img_path, knn_clf = None, model_save_path ="", DIST_THRESH = .5):
    """
    recognizes faces in given image, based on a trained knn classifier

    :param X_img_path: path to image to be recognized
    :param knn_clf: (optional) a knn classifier object. if not specified, model_save_path must be specified.
    :param model_save_path: (optional) path to a pickled knn classifier. if not specified, model_save_path must be knn_clf.
    :param DIST_THRESH: (optional) distance threshold in knn classification. the larger it is, the more chance of misclassifying an unknown person to a known one.
    :return: a list of names and face locations for the recognized faces in the image: [(name, bounding box), ...].
        For faces of unrecognized persons, the name 'N/A' will be passed.
    """

    if not isfile(X_img_path) or splitext(X_img_path)[1][1:] not in ALLOWED_EXTENSIONS:
        raise Exception("invalid image path: {}".format(X_img_path))

    if knn_clf is None and model_save_path == "":
        raise Exception("must supply knn classifier either thourgh knn_clf or model_save_path")

    if knn_clf is None:
        with open(model_save_path, 'rb') as f:
            knn_clf = pickle.load(f)

    X_img = face_recognition.load_image_file(X_img_path)
    X_faces_loc = face_locations(X_img)
    if len(X_faces_loc) == 0:
        return []

    faces_encodings = face_recognition.face_encodings(X_img, known_face_locations=X_faces_loc)


    closest_distances = knn_clf.kneighbors(faces_encodings, n_neighbors=1)

    is_recognized = [closest_distances[0][i][0] <= DIST_THRESH for i in range(len(X_faces_loc))]

    # predict classes and cull classifications that are not with high confidence
    return [(pred, loc) if rec else ("N/A", loc) for pred, loc, rec in zip(knn_clf.predict(faces_encodings), X_faces_loc, is_recognized)]

def createdir(path):
    if not exists( dirname(path) ) :
        createdir( dirname(path) )
    if not exists(path):
        print("Create Directory:%s" % (path))
        mkdir(path, 755)

def draw_preds(img_path, preds, filesta, basedir):
    """
    shows the face recognition results visually.

    :param img_path: path to image to be recognized
    :param preds: results of the predict function
    :return:
    """
    prefix2 = basename(img_path).split("_who")[0]

    source_img = Image.open(img_path).convert("RGBA")
    draw = ImageDraw.Draw(source_img)
    imname = ''
    for pred in preds:
        loc = pred[1]
        name = pred[0]
        # (top, right, bottom, left) => (left,top,right,bottom)
        draw.rectangle(((loc[3], loc[0]), (loc[1],loc[2])), outline="red")
        draw.text((loc[3], loc[0] - 30), name, font=ImageFont.truetype('Pillow/Tests/fonts/FreeMono.ttf', 30))
        print("name:%s(%d) %s,%s" % (name, len(name), name.find("N/A")>=0, name.find('N/A')>=0))
        cropimg = source_img.crop((loc[3], loc[0], loc[1], loc[2]))
        imname = "%s/whois/%s/%s_found_%s.png" % (basedir, name, prefix2, datetime.datetime.now().strftime("%Y%m%d%H%M%S-%f"))
        if str(name).find("N/A") >= 0:
            #assert(0)
            imname=imname.replace("_found_", "_unmatched_")
            imname=imname.replace("N/A", "whowho/")
        else:
            pass
        print("imname:%s" % imname)
        if not exists(dirname(imname)):
            #mkdir(dirname(imname), 755)
            createdir( dirname(imname))
            print("Create folder %s"%(dirname(imname)))
        if not imname.upper().find("SEULKI") >= 0:
            cropimg.save(imname)
        if not filesta.get(name):
            filesta[name] = 1
        else:
            filesta[name] = filesta[name] + 1

    #source_img.show()
    if False and len(imname) :
        source_img.save("%s" % (imname.replace("whois/", "whois/total_")))

def processremainframe(frames, outputfolder, videofile):
    count_found = 0
    for frame in frames:
        rgb_frame = frame[0][:, :, ::-1]

        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if len(face_encodings):
            print("Found %d from Queue (No.%d)" % (len(face_encodings), frame[1]))
            img_path = "%s/%s_frame%04d_who.jpg" % (outputfolder, basename(videofile).split(".")[0], frame[1])
            cv2.imwrite(img_path, frame[0])
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

        #if frame_number & 0x1f : continue
        #if flag_found: flag_found = flag_found -1
        #elif not frame_number % 15 == 0 : continue
        #if not frame_number % unit_per_frame == 0: continue
        if flag_count or skip_count >= MAXSKIPCOUNT:
            skip_count = 0
        elif skip_count < MAXSKIPCOUNT:
            skip_count += 1
            if len(myq)>5: myq.pop(0)
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
            cv2.imwrite(img_path, frame)
            flag_count = MAXCHECKLIFE
            found_count += 1
            if found_count > 100: break
            if len(myq):
                found_count += processremainframe(myq, outputfolder, videofile)
                myq = []
        elif flag_count > 0:
            flag_count = flag_count - 1

    # All done!
    input_movie.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("--train", dest="trainfolder",
                      help="specify folder to train for machine learning.",
                      type='string',
                      default='/mnt/hgfs/shareforvm/face/train')
    ## /mnt/hgfs/shareforvm/face/train
    ## /home/deeplearning/Desktop/face_recognition examples/knn_examples/train

    parser.add_option("--tempout", dest="outputfolder",
                      help="specify folder to store teporary image file from video.",
                      type='string',
                      default='/home/deeplearning/Desktop/face_recognition examples/output')

    parser.add_option("--target", dest="targetfolder",
                      help="specify folder to read video files .",
                      type='string',
                      default='/home/deeplearning/nasshare/chitack.chang/face/ipdisk/target0912')

    parser.add_option("--recognition", dest="recognition",
                      help="specify folder to distribute each face",
                      type='string',
                      default='/home/deeplearning/nasshare/chitack.chang/face/whowho')

    (options, args) = parser.parse_args()

    knn_clf = train(options.trainfolder)

    allfilesta = {}
    for item in listdir(options.targetfolder):
        if isdir(join(options.targetfolder, item)):
            continue
        if item.upper().find(".MOV") >= 0:
            if not exists(options.outputfolder):
                mkdir(options.outputfolder, 755)
            start = datetime.datetime.now()
            print(start)
            CheckVideo(join(options.targetfolder, item), options.outputfolder)
            finish = datetime.datetime.now()
            print("Elapsed %s" % (finish - start))

            prefix = basename(item).split("_")[0]


            filesta = {}
            img_file_list = glob.glob( options.outputfolder + "/%s*" % (item.split(".")[0]))
            #print(img_file_list, options.outputfolder + "/%s*" % (item.split(".")[0]))
            totalcount = len(img_file_list)
            index = 1
            img_file_list.sort()
            for img_path in img_file_list:
                print("%d/%5d" % (index, totalcount))
                index = index + 1
                preds = predict(img_path ,knn_clf=knn_clf)
                draw_preds(img_path, preds, filesta, options.recognition)

            #print(sorted(filesta.items(), key=lambda t: t[1], reverse=True))

            allfilesta[prefix] = filesta

    for fn in sorted(allfilesta):
        #print("File : %s" % item, filesta[item])
        print(fn)
        #print(sorted(allfilesta[fn].items(), key=lambda t: t[1], reverse = True))
        if allfilesta[fn].get('seulki') : allfilesta[fn].pop('seulki')
        newlist = sorted(allfilesta[fn].items(), key=lambda t: t[1], reverse=True)
        for i in newlist:
            print("%10s, %4d, %2.1f%%" % (i[0], allfilesta[fn][i[0]], allfilesta[fn][i[0]]*100/sum(allfilesta[fn].values())))

