import array
import asyncio
import os
import json
import tkinter
from tkinter import filedialog
import pyexiv2
import cloudinary
import datetime
import time
import numpy as np
from PIL import ImageTk, Image
import pymongo
from pymongo.server_api import ServerApi
import pickle
from bson import ObjectId
from pathlib import Path

# from tkinter import *
# Explicit imports to satisfy Flake8
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, ttk
from tkinter import *

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path("./assets")

# Reading config values
with open('config/cloudinary.json', 'r') as cloudinary_config_file:
    txt = cloudinary_config_file.read()
    cloudinary_config_dict = json.loads(txt)
with open('config/mongoDb.json', 'r') as mongodb_config_file:
    txt = mongodb_config_file.read()
    mongodb_config_dict = json.loads(txt)
f_error = open('output/errors.txt', 'w')
f_error.write("No errors")
f_error.close()
cloudinary_config_file.close()
mongodb_config_file.close()

# cloudinary configuring
cloudinary.config(
    cloud_name=cloudinary_config_dict["cloud_name"],
    api_key=cloudinary_config_dict["api_key"],
    api_secret=cloudinary_config_dict["api_secret"],
    secure=cloudinary_config_dict["secure"]
)

import cloudinary.uploader
import cloudinary.api

# mongoDb configuration
Mongo_client = pymongo.MongoClient("mongodb+srv://bzs:" + mongodb_config_dict[
    "password"] + "@cluster0.jldup.mongodb.net/?retryWrites=true&w=majority", server_api=ServerApi('1'),
                                   serverSelectionTimeoutMS=5000)
db = Mongo_client[mongodb_config_dict["db_name"]]
collection = db[mongodb_config_dict["collection_name"]]



def changeConfigValues():
    with open('config/mongoDb.dictionary', 'wb') as mongodb_config_file_write:
        pickle.dump(mongodb_config_dict, mongodb_config_file_write)
    with open('config/cloudinary.json', 'wb') as cloudinary_config_file_write:
        pickle.dump(cloudinary_config_dict, cloudinary_config_file_write)



def returnDict(a):
    return {"_id": a}


def decadeCalculator(year):
    firstThreedigits = int(year / 10)
    decade = firstThreedigits * 10
    return str(decade) + 'er'


def findDuplicates():
    ProgressBar['value'] = 0
    main_label.config(text="Looking for duplicates...", bg="Yellow")
    window.update_idletasks()
    allMags = list(collection.aggregate(
        [
            {"$group": {"_id": "$SKU", "unique_ids": {"$addToSet": "$_id"}, "count": {"$sum": 1}}},
            {"$match": {"count": {"$gte": 2}}}
        ]
    ))
    if len(list(allMags)) == int(0):
        main_label.config(text="No duplicates found", bg="Green")
    else:
        intervalLength = 100 / len(list(allMags))
        ProgressBar.config(length=100, mode="determinate", value=1)
        main_label.config(text="Found "+str(len(list(allMags)))+" duplicates", bg="Orange")
        for document in allMags:
            duplicatesToBeDeleted = document["unique_ids"][1:len(document["unique_ids"])]
            arr = map(returnDict, duplicatesToBeDeleted)
            for a in list(arr):
                collection.delete_one(a)
            ProgressBar['value'] += intervalLength
            window.update_idletasks()
        main_label.config(text="Deleted " + str(len(list(allMags))) + " duplicates", bg="Green")


months = {
    "01": 31,
    "02": 28,
    "03": 31,
    "04": 30,
    "05": 31,
    "06": 30,
    "07": 31,
    "08": 31,
    "09": 30,
    "10": 31,
    "11": 30,
    "12": 31
}
finalOutput = []
jsonModel = {
    "SKU": "",
    "Name": "",
    "FileName": "",
    "Date": "",
    "Ausgabe": "",
    "Publication": "",
    "Publicationfrequencies": "",
    "Published": 1,
    "Isfeatured": 0,
    "Shortdescription": "",
    "Description": "Description",
    "Bewertung": -1,
    "Instock": 1,
    "Saleprice": "",
    "Preis": "",
    "Jahr": 0,
    "Jahrzehnt": [],
    "Monat": [],
    "Tag": [],
    "ZEITSCHRIFTEN": [],
    "THEMA": [],
    "PERSÖNLICHKEITEN": [],
    "ORT": [],
    "MOTIV": [],
    "Titelseite": [],
    "Tags": [],
    "Images": "",
    "imglink": "",
    "sort": 0,
}
ImageFolder = ""


def selectFolder():
    ProgressBar["value"] = 0
    window.update_idletasks()
    global ImageFolder
    ImageFolder = filedialog.askdirectory()
    if ImageFolder != "":
        button_2.config(state="active")
        main_label.config(text="Folder selected successfully start extracting", bg="Green")
    else:
        button_2.config(state="disabled")
        main_label.config(text="No folder was selected", bg="Red")


def uploadJson(Obj):
    try:
        x = collection.insert_one(dict(Obj))
    except Exception as e:
        print(e)


def findMonths(Ausgabe, Publication, YEAR):
    if Publication == "W":
        WEEK = Ausgabe - 1  # as it starts with 0 and you want week to start from monday
        startdate = time.asctime(time.strptime(str(YEAR) + ' %d 0' % WEEK, '%Y %W %w'))
        startdate = datetime.datetime.strptime(startdate, '%a %b %d %H:%M:%S %Y')
        dates = [startdate.strftime('%m')]
        day = startdate + datetime.timedelta(days=7)
        dates.append(day.strftime('%m'))
        if dates[0] == dates[-1]:
            return [dates[0]]
        else:
            return dates
    elif Publication == "W2":
        WEEK = Ausgabe - 1  # as it starts with 0 and you want week to start from monday
        startdate = time.asctime(time.strptime(str(YEAR) + ' %d 0' % WEEK, '%Y %W %w'))
        startdate = datetime.datetime.strptime(startdate, '%a %b %d %H:%M:%S %Y')
        dates = [startdate.strftime('%m')]
        day = startdate + datetime.timedelta(days=15)
        dates.append(day.strftime('%m'))
        if dates[0] == dates[-1]:
            return [dates[0]]
        else:
            return dates
    elif Publication == "M2":
        return Ausgabe * 2
    elif Publication == "M":
        return Ausgabe


def frequencyAssign(Info2):
    if Info2.lower() == "w":
        jsonModel["Publicationfrequencies"] = "52 to 53 issues/year"
        jsonModel["Publication"] = "W"
    elif Info2.lower() == "w2" or "2w":
        jsonModel["Publicationfrequencies"] = "26 to 27 issues / year"
        jsonModel["Publication"] = "W2"
    elif Info2.lower() == "m2" or "2m":
        jsonModel["Publicationfrequencies"] = "every 2 months an issue"
        jsonModel["Publication"] = "M2"
    elif Info2.lower() == "m":
        jsonModel["Publicationfrequencies"] = "12 issues/year"
        jsonModel["Publication"] = "M"


def calculateBiWeekly(WEEK, YEAR):
    Tags = []
    WEEK = WEEK - 1  # as it starts with 0 and you want week to start from monday
    startdate = time.asctime(time.strptime(str(YEAR) + ' %d 0' % WEEK, '%Y %W %w'))
    startdate = datetime.datetime.strptime(startdate, '%a %b %d %H:%M:%S %Y')
    dates = [startdate.strftime('%d')]
    for i in range(1, 15):
        day = startdate + datetime.timedelta(days=i)
        dates.append(day.strftime('%d'))
    return dates


def calculateDays(WEEK, YEAR):
    Tags = []
    WEEK = WEEK - 1  # as it starts with 0 and you want week to start from monday
    startdate = time.asctime(time.strptime(str(YEAR) + ' %d 0' % WEEK, '%Y %W %w'))
    startdate = datetime.datetime.strptime(startdate, '%a %b %d %H:%M:%S %Y')
    dates = [startdate.strftime('%Y-%m-%d')]
    for i in range(1, 8):
        day = startdate + datetime.timedelta(days=i)
        dates.append(day.strftime('%Y-%m-%d'))
    first = dates[1].split("-")
    if months[first[1]] - int(first[-1]) >= 7:
        for i in range(int(first[2]), int(first[2]) + 7):
            Tags.append(i)
    elif months[first[1]] - int(first[-1]) >= 3:
        for i in range(int(first[2]), months[str(int(int(first[1]))).zfill(2)] + 1):
            Tags.append(i)
    else:
        for i in range(1, (7 - (months[first[1]] - int(first[-1])))):
            Tags.append(i)
    return Tags


def uploadImage(filename, skuCaps):
    global ImageFolder
    x = cloudinary.uploader.upload(ImageFolder + '/' + filename,
                                   folder="images",
                                   public_id=skuCaps,
                                   overwrite=True,
                                   resource_type="image",
                                   moderation="duplicate:0.8")


def mainLoop():
    ProgressBar["value"] = 0
    window.update_idletasks()
    calculateBiWeekly(17, 1922)
    if ImageFolder == " ":
        main_label.config(text="Select a valid folder", bg="Red")
    else:
        AllImagesInInput = os.listdir(ImageFolder)
        print(len(AllImagesInInput))
        if len(AllImagesInInput) < 1:
            main_label.config(text="No images found in the folder", bg="Orange")
        else:
            error_count=0
            main_label.config(text="Extracting data from "+str(len(AllImagesInInput)) +" Images.", bg="Yellow")
            output = []
            count = 1
            ProgressBar.config(length=100, mode="determinate", value=1)
            intervalLength = 100 / len(AllImagesInInput)
            f = open("./output/Data.json", "w", encoding="utf-8")
            f.write("[")
            sort = 1
            f_error = open('output/errors.txt', 'w')
            for img in AllImagesInInput:
                main_label.config(text="Extracting data from "+str(len(AllImagesInInput)) +" Images.", bg="Yellow")
                window.update_idletasks()
                jsonModel['Jahrzehnt'].clear()
                jsonModel['Monat'].clear()
                jsonModel['Tag'].clear()
                jsonModel["ZEITSCHRIFTEN"].clear()
                jsonModel["THEMA"].clear()
                jsonModel["PERSÖNLICHKEITEN"].clear()
                jsonModel["ORT"].clear()
                jsonModel["MOTIV"].clear()
                jsonModel["Titelseite"].clear()
                jsonModel["Tags"].clear()
                try:
                    time.sleep(0.01)
                    metadata = pyexiv2.Image(ImageFolder + '/' + img)
                    data = metadata.read_iptc()
                    Info = img.split(" ")
                    jsonModel["SKU"] = img.split(".")[0].lower().replace(" ", "-")
                    if len(Info) > 4:
                        length = len(Info)
                        Name = ""
                        for i in range(0, length - 4 + 1):
                            Name += Info[i] + " "
                        Name = Name.rstrip(Name[-1])
                        jsonModel["Name"] = Name
                    else:
                        jsonModel["Name"] = Info[0]
                    jsonModel['Jahrzehnt'].append(decadeCalculator(int(Info[-3])))
                    jsonModel["Jahr"] = Info[-3]
                    jsonModel["FileName"] = img.split(".")[0].replace(" ", " ")
                    jsonModel["Date"] = Info[-3] + " " + Info[-2].lower() + " " + Info[-1].split(".")[0]
                    jsonModel["Ausgabe"] = Info[-1].split(")")[0].split("(")[1]
                    frequencyAssign(Info[-2])
                    jsonModel["Images"] = "images/" + img.replace(" ", "-")
                    jsonModel["imglink"] = img.replace(" ", "-")
                    if sort == 0:
                        sort = 1
                    jsonModel["sort"] = sort
                    sort = (sort + 1) % 100

                    jsonModel["Monat"] = findMonths(int(jsonModel["Ausgabe"]), jsonModel["Publication"],
                                                    jsonModel["Jahr"])
                    # To decide days
                    if jsonModel["Publication"] == "W":
                        Days = calculateDays(int(jsonModel["Ausgabe"]), int(jsonModel["Jahr"]))
                        jsonModel["Tag"] = Days
                    elif jsonModel["Publication"] == "W2":
                        Days = calculateBiWeekly(int(jsonModel["Ausgabe"]), int(jsonModel["Jahr"]))
                        jsonModel["Tag"] = Days
                    elif jsonModel["Publication"] == "M2":
                        jsonModel["Tag"] = np.arange(1, months[jsonModel["Ausgabe"] * 2] + 1)
                    elif jsonModel["Publication"] == "M":
                        jsonModel["Tag"] = np.arange(1, months[jsonModel["Ausgabe"]] + 1)
                    # Image extraction

                    for a in data['Iptc.Application2.Keywords']:
                        keyValue = a.split(":")
                        if len(keyValue) > 1:
                            if keyValue[0] == "PREIS":
                                keyValue[0] = keyValue[0].capitalize()
                                jsonModel[keyValue[0]] = keyValue[-1]
                            elif keyValue[0] == "Titelseite":
                                if keyValue[-1] not in jsonModel[keyValue[0]]:
                                    jsonModel[keyValue[0]].append(keyValue[-1])
                            elif keyValue[0] == "Bewertung" or keyValue[0] == "BEWERTUNG":
                                jsonModel[keyValue[0].capitalize()] = keyValue[-1]
                            else:
                                if keyValue[-1] not in jsonModel[keyValue[0].upper()]:
                                    jsonModel[keyValue[0].upper()].append(keyValue[-1])
                        else:
                            break
                    f.write(json.dumps(jsonModel, ensure_ascii=False))
                    if bool(mongodb_config_dict["JsonUpload"]):
                        main_label.config(text="Uploading json to mongodb")
                        window.update_idletasks()
                        uploadJson(dict(jsonModel))
                    if bool(cloudinary_config_dict["ImageUpload"]):
                        main_label.config(text="Uploading Image to cloudinary")
                        window.update_idletasks()
                        x = cloudinary.uploader.upload(ImageFolder + '/' + img,
                                                       folder="images",
                                                       public_id=jsonModel['SKU'],
                                                       overwrite=True,
                                                       resource_type="image")
                    main_label.config(text="Extracting data from images...", bg="Yellow")
                    ProgressBar['value'] += intervalLength
                    window.update_idletasks()
                    if count < len(AllImagesInInput):
                        f.write(",")
                    count += 1

                except Exception as e:
                    error_count+=1
                    f_error.write(img + " : " + str(e) + '\n')

                    ProgressBar['value'] += intervalLength
                    window.update_idletasks()
                    count += 1
            f_error.close()
            f.write("]")
            f.close()
            main_label.config(text="Successfully created data for "+str(len(AllImagesInInput)-error_count)+" images out of "+str(len(AllImagesInInput)), bg="Green")


# Initialising window


def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)


window = Tk()
window.title("BZS Image Tool")



# window.state("iconic")
# window.resizable(False, False)
window.configure(bg="#E5E5E5")

canvas = Canvas(
    window,
    bg="#E5E5E5",
    height=1024,
    width=1440,
    bd=0,
    highlightthickness=0,
    relief="ridge"
)

canvas.place(x=0, y=0)
image_image_1 = PhotoImage(
    file=relative_to_assets("Image_1.png"))
image_1 = canvas.create_image(
    720.0,
    512.0,
    image=image_image_1
)

button_image_1 = PhotoImage(
    file=relative_to_assets("Button_1.png"))
button_1 = Button(
    image=button_image_1,
    borderwidth=0,
    highlightthickness=0,
    command=findDuplicates,
    relief="flat",
)
button_1.place(
    x=616.0,
    y=727.0,
    width=208.0,
    height=54.0
)

button_image_2 = PhotoImage(
    file=relative_to_assets("Button_2.png"))
button_2 = Button(
    image=button_image_2,
    borderwidth=0,
    highlightthickness=0,
    command=mainLoop,
    relief="flat",
    state="disabled"
)
button_2.place(
    x=616.0,
    y=661.0,
    width=208.0,
    height=54.0
)

button_image_3 = PhotoImage(
    file=relative_to_assets("Button_3.png"))
button_3 = Button(
    image=button_image_3,
    borderwidth=0,
    highlightthickness=0,
    command=selectFolder,
    relief="flat",
)
button_3.place(
    x=616.0,
    y=595.0,
    width=208.0,
    height=54.0
)
ProgressBar = ttk.Progressbar(mode='determinate')

ProgressBar.place(
    x=395.0,
    y=480,
    width=650,
    height=30
)

main_label = Label(text="Please select the image folder(*should only contain images in it)", font=30, textvariable="")
main_label.config(bg="#E5E5E5")
main_label.place(
    x=395,
    y=372,
    width=650,
    height=54
)
# canvas.create_rectangle(
#     395.0,
#     480.0,
#     1045.0,
#     545.0,
#     fill="#000000",
#     outline="")
# window.resizable(False, False)

window.mainloop()
