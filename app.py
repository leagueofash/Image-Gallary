__author__ = "Ashraf"

import datetime
import os
from flask import Flask
from flask import render_template
from flask import request
from flask import send_from_directory
from werkzeug.utils import secure_filename
import pymongo

app=Flask(__name__)
URI = "mongodb://127.0.0.1:27017" #setting up the path of MongoDB, always runs on 27017, if not then chenge the port
UPLOAD_FOLDER= os.path.dirname(os.path.abspath(__file__))  #set up path of upload folder
ALLOWED_EXTENSIONS = set(['jpeg','jpg','gif','png']) #extension allowed list
client = pymongo.MongoClient(URI) #initialize the MongoDB
DB = client['upload_details'] #DB that would be used, if not there MongoDB creates one for you, no worries
images = DB.images #collection(table)that would be used, if not there MongoDB creates one for you, no worries
limit =10 #limit to number of images per page
offset=0 #begining og offset

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
#Function that defines the root of the webapp, i.e. what URL should open first after entering the URL. In this case it is calling the get_gallery()
#that would render all the images
@app.route("/")
def index():
    return get_gallery()

#This is the upload function, where all the upload is happening
@app.route("/upload ", methods=["POST"])
def upload():

    saving_address=os.path.join(UPLOAD_FOLDER, 'images') #set-up the image folder

    if not os.path.isdir(saving_address): #is image folder is not found, then create one
        os.mkdir(saving_address)
    elif os.path.isdir(saving_address):
        file = request.files.get('file') #get files that are uploaded in the html page and store them in file, we can use multiple files as well, need to ceate a for loop
        description = request.form['description'] #get the caption and store it in description
        if file and allowed_file(file.filename): #check the extensions of the filename by calling the function allowed_file
            filename = secure_filename(file.filename) #this function helps prevent filename based attacks
            destination = "/".join([saving_address, filename])
            images.insert_one({"filename": filename, "description": description, "date": datetime.datetime.utcnow()}) #insert image into image collection of the database
            file.save(destination) #save the file in filesystem
            return get_gallery()
        else:
            return render_template("notsupported.html") #if file format not supported, render notsupported.html page on the browser
    else:
        print("Couldn't create upload directory {}".format(saving_address))

@app.route('/upload/<filename>')
def send_image(filename):
    return send_from_directory("images",filename) #this function will get the images from the images dorectory and send it to the gallery.html <img>tag where it is rendered

@app.route('/NextPage', methods=['POST'])
def increment():
    global offset
    offset = offset+10 #increase the value of offset by 10, this will let us fetch 10 images from DB
    return get_gallery()

@app.route('/Upload', methods=['POST'])
def uploadimage():
    return render_template("upload.html")

@app.route('/PrevPage', methods=['POST'])
def decrement():
    global offset
    if offset == 0: #if offset goes below 10, then this will reintialize the counter to 0 and render all the images from start
        return get_gallery()
    else:
        offset = offset-10 #if the counter is greater than 10, then everytime it reduces it by 10
        return get_gallery()

@app.route('/back_to_gallery')
def reset():
    global offset
    offset=0
    return get_gallery()

@app.route('/gallery', methods=['GET'])
def get_gallery():
    starting_id = images.find().sort("_id",pymongo.DESCENDING) #this will sort the db based on ID, and will return the forst element
    last_id = starting_id[offset]["_id"] #this will return the last id based on offset, so if offset is 10, ;ast id return would be the 10th id in db
    image_names = [a['filename'] for a in images.find({"_id": {"$lte": last_id}}).sort("_id",pymongo.DESCENDING).limit(limit)] #fetch 10 elements froom DB
    caption = [a['description'] for a in images.find({"_id": {"$lte": last_id}}).sort("_id",pymongo.DESCENDING).limit(limit)]
    image_names= list(filter(None, image_names)) #this will remove all empty rows that were returned by DB
    caption= list(filter(None, caption))
    return render_template("gallery.html", image_names=image_names, caption=caption) #rendering on the page

@app.errorhandler(500)
def page_not_found(error):
    return render_template('page_not_found.html'), 500 #any 500 error page would be redirected to this page

if __name__ == "__main__":
    app.run(port=5555)