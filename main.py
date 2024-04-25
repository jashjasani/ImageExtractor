import math
import os
import json
import unicodedata
from tkinter import filedialog
from PIL import ImageTk, Image
import pyexiv2
import cloudinary
import time
from datetime import datetime
from isoweek import Week
import numpy as np
import sys
import pymongo
from pymongo.server_api import ServerApi
import pickle
from pathlib import Path
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, ttk, Label, Toplevel,BooleanVar, Checkbutton

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path("./assets")

with open('config/cloudinary.json', 'r') as cloudinary_config_file:
    txt = cloudinary_config_file.read()
    cloudinary_config_dict = json.loads(txt)

with open('config/mongoDb.json', 'r') as mongodb_config_file:
    txt = mongodb_config_file.read()
    mongodb_config_dict = json.loads(txt)

f_error = open('output/errors.txt', 'w')
f_error.write("No errors")
f_error.close()

cloudinary.config(
    cloud_name=cloudinary_config_dict["cloud_name"],
    api_key=cloudinary_config_dict["api_key"],
    api_secret=cloudinary_config_dict["api_secret"],
    secure=cloudinary_config_dict["secure"]
)

import cloudinary.uploader
import cloudinary.api

Mongo_client = pymongo.MongoClient("mongodb+srv://bzs:" + mongodb_config_dict[
    "password"] + "@cluster0.jldup.mongodb.net/?retryWrites=true&w=majority", server_api=ServerApi('1'),
                                   serverSelectionTimeoutMS=5000)
db = Mongo_client[mongodb_config_dict["db_name"]]
collection = db[mongodb_config_dict["collection_name"]]

def changeConfigValues():
    with open('config/mongoDb.json', 'w') as mongodb_config_file_write:
        json.dump(mongodb_config_dict, mongodb_config_file_write, indent=4)

    with open('config/cloudinary.json', 'w') as cloudinary_config_file_write:
        json.dump(cloudinary_config_dict, cloudinary_config_file_write, indent=4)


def returnDict(a):
    return {"_id": a}

def decadeCalculator(year):
    firstThreedigits = int(year / 10)
    decade = firstThreedigits * 10
    return str(decade) + 'er'

def findDuplicates():
    status_image.config(image='')
    ProgressBar['value'] = 0
    main_label.config(text="Looking for duplicates...", bg="#BF8563")
    window.update_idletasks()
    allMags = list(collection.aggregate(
        [
            {"$group": {"_id": "$SKU", "unique_ids": {"$addToSet": "$_id"}, "count": {"$sum": 1}}},
            {"$sort": {"_id": -1}},
            {"$match": {"count": {"$gte": 2}}}
        ]
    ))
    if len(list(allMags)) == int(0):
        main_label.config(text="No duplicates found", bg="#A4A67C")
        status_image.config(image=greenImage)
    else:
        intervalLength = 100 / len(list(allMags))
        ProgressBar.config(length=100, mode="determinate", value=1)
        main_label.config(text="Found " + str(len(list(allMags))) + " duplicates", bg="Orange")
        for document in allMags:
            duplicatesToBeDeleted = document["unique_ids"][1:len(document["unique_ids"])]
            arr = map(returnDict, duplicatesToBeDeleted)
            for a in list(arr):
                collection.delete_one(a)
            ProgressBar['value'] += intervalLength
            window.update_idletasks()
        main_label.config(text="Deleted " + str(len(list(allMags))) + " duplicates", bg="#A4A67C")
        status_image.config(image=greenImage)

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
    "12": 31,
    1: 31,
    2: 28,
    3: 31,
    4: 30,
    5: 31,
    6: 30,
    7: 31,
    8: 31,
    9: 30,
    10: 31,
    11: 30,
    12: 31
}

monthnames = {
    1: "Jänner",
    2: "Februar",
    3: "März",
    4: "April",
    5: "Mai",
    6: "Juni",
    7: "Juli",
    8: "August",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Dezember"
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
    "QUELLE" : "",

}

ImageFolder = ""

def selectFolder():
    status_image.config(image='')
    ProgressBar['value'] = 0
    window.update_idletasks()
    global ImageFolder
    ImageFolder = filedialog.askdirectory()
    if ImageFolder != "":
        button_2.config(state="active")
        main_label.config(text="Folder selected successfully start extracting", bg="#A4A67C")
    else:
        status_image.config(image='')
        button_2.config(state="disabled")
        main_label.config(text="No folder was selected", bg="#A66073")

def uploadJson(Obj):
    try:
        x = collection.insert_one(dict(Obj))
    except Exception as e:
        print(e)

def findMonths(Ausgabe, Publication, YEAR):
    monthnames = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
        7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    
    if Publication == "W":
        if Ausgabe == 53:
            Ausgabe -= 1
        week1 = Week(year=YEAR, week=Ausgabe).days()
        date = [datetime.strftime(week1[0], '%m'), datetime.strftime(week1[-1], '%m')]
        if date[0] == date[-1]:
            return [monthnames.get(int(date[0]))]
        else:
            return [monthnames.get(int(date[0])), monthnames.get(int(date[-1]))]
    elif Publication == "W4":
        if Ausgabe == 13:
            return [monthnames[12]]
        else:
            return [monthnames[int(Ausgabe)]]
    elif Publication == "W2":
        if Ausgabe == 27:
            Ausgabe -= 1
        
        week1 = Week(year=YEAR, week=2 * Ausgabe - 1 ).days()
        week2 = Week(year=YEAR, week=2 * Ausgabe).days()
        
        
        # Ensure week2 is a list of dates
        date = [datetime.strftime(week1[0], '%m'), datetime.strftime(week2[-1], '%m')]
        if date[0] == date[-1]:
            return [monthnames.get(int(date[0]))]
        else:
            return [monthnames.get(int(date[0])), monthnames.get(int(date[-1]))]
    elif Publication == "M2":
        return [monthnames[Ausgabe * 2 - 1], monthnames[Ausgabe * 2]]
    elif Publication == "M":
        return [monthnames[Ausgabe]]
    elif Publication == "M3":
        return [monthnames[math.ceil(Ausgabe / 3)]]
    elif Publication == "J":
        return list(monthnames.values())
    elif Publication == "HJ":
        if Ausgabe == 1:
            MONTHS = list(monthnames.values())[:6]
            return MONTHS
        else:
            MONTHS = list(monthnames.values())[6:]
            return MONTHS
    elif Publication == "Q":
        if Ausgabe == 1:
            return list(monthnames.values())[:3]
        elif Ausgabe == 2:
            return list(monthnames.values())[3:6]
        elif Ausgabe == 3:
            return list(monthnames.values())[6:9]
        elif Ausgabe == 4:
            return list(monthnames.values())[9:]
    elif Publication == "J24":
        return [monthnames[math.ceil(Ausgabe / 2)]]
    

def frequencyAssign(Info2):
    if Info2.lower() == "w":
        jsonModel["Publicationfrequencies"] = "52 to 53 issues/year"
        jsonModel["Publication"] = "W"
    elif Info2.lower() == "w2" or Info2.lower() == "2w":
        jsonModel["Publicationfrequencies"] = "26 to 27 issues / year"
        jsonModel["Publication"] = "W2"
    elif Info2.lower() == "m2" or Info2.lower() == "2m":
        jsonModel["Publicationfrequencies"] = "every 2 months an issue"
        jsonModel["Publication"] = "M2"
    elif Info2.lower() == "m":
        jsonModel["Publicationfrequencies"] = "12 issues/year"
        jsonModel["Publication"] = "M"
    elif Info2.lower() == "w4" or Info2.lower() == "4w":
        jsonModel["Publicationfrequencies"] = "13 issues/year"
        jsonModel["Publication"] = "W4"
    elif Info2.lower() == "j":
        jsonModel["Publicationfrequencies"] = "1 issue/year"
        jsonModel["Publication"] = "J"
    elif Info2.lower() == "j24" or Info2.lower() == "24j":
        jsonModel["Publicationfrequencies"] = "24 issues per year"
        jsonModel["Publication"] = "J24"
    elif Info2.lower() == "hj":
        jsonModel["Publicationfrequencies"] = "2 issues per year"
        jsonModel["Publication"] = "HJ"
    elif Info2.lower() == "q":
        jsonModel["Publicationfrequencies"] = "4 issues per year"
        jsonModel["Publication"] = "Q"
    elif Info2.lower() == "m3" or Info2.lower() == "3m":
        jsonModel["Publicationfrequencies"] = "36 issues per year"
        jsonModel["Publication"] = "M3"

def calculateBiWeekly(WEEK, YEAR):
    if WEEK == 27:
        WEEK -= 1
    week1 = Week(year=YEAR, week=2 * WEEK - 1 ).days()
    week2 = Week(year=YEAR, week=2 * WEEK).days()
    dates = []
    for d in week1:
        dates.append(datetime.strftime(d, '%d'))
    for d in week2:
        dates.append(datetime.strftime(d, '%d'))
    return dates

def calculateDays(WEEK, YEAR):
    if WEEK == 53 and len(list(Week.weeks_of_year(YEAR))) == 53:
        week = Week(year=YEAR, week=WEEK).days()
        dates = []
        for d in week:
            dates.append(datetime.strftime(d, '%d'))
        return dates
    else:
        if WEEK == 53:
            WEEK -= 1
        week = Week(year=YEAR, week=WEEK).days()
        dates = []
        for d in week:
            dates.append(datetime.strftime(d, '%d'))
        return dates


def mainLoop():
    ProgressBar['value'] = 0
    window.update_idletasks()
    if ImageFolder == " ":
        main_label.config(text="Select a valid folder", bg="Red")
        return
    AllImagesInInput = [unicodedata.normalize('NFC', f) for f in os.listdir(ImageFolder)]
    if len(AllImagesInInput) < 1:
        main_label.config(text="No images found in the folder", bg="Orange")
        return
    error_count = 0
    main_label.config(text="Extracting data from " + str(len(AllImagesInInput)) + " Images.", bg="#BF8563")
    output = []
    count = 1
    ProgressBar.config(length=100, mode="determinate", value=1)
    intervalLength = 100 / len(AllImagesInInput)
    f = open("./output/Data.json", "w", encoding="utf-8")
    f.write("[")
    sort = 1
    f_error = open('output/errors.txt', 'w')
    for img in AllImagesInInput:
        jsonModel["QUELLE"] = ""
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
            metadata = pyexiv2.Image(ImageFolder + '/' + img, encoding='iso-8859-1')
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
            jsonModel["Jahr"] = int(Info[-3])
            jsonModel["FileName"] = img.split(".")[0].replace(" ", " ")
            jsonModel["Date"] = Info[-3] + " " + Info[-2].lower() + " " + Info[-1].split(")")[0].split("(")[1]
            jsonModel["Ausgabe"] = int(Info[-1].split(")")[0].split("(")[1]) 
            frequencyAssign(Info[-2])
            imageId = jsonModel["Name"].replace(" ", "_") + "_" + str(jsonModel["Jahr"]) + "_" + jsonModel[
                "Publication"].lower() + "_" + str(jsonModel["Ausgabe"])
            jsonModel["Images"] = "images/" + imageId
            jsonModel["imglink"] = imageId
            if sort == 0:
                sort = 1
            jsonModel["sort"] = sort
            sort = (sort + 1) % 100
            jsonModel["Monat"] = findMonths(int(jsonModel["Ausgabe"]), jsonModel["Publication"],
                                            jsonModel["Jahr"])
            if jsonModel["Publication"] == "W":
                Days = calculateDays(int(jsonModel["Ausgabe"]), int(jsonModel["Jahr"]))
                jsonModel["Tag"] = Days
            elif jsonModel["Publication"] == "W2":
                Days = calculateBiWeekly(int(jsonModel["Ausgabe"]), int(jsonModel["Jahr"]))
                jsonModel["Tag"] = Days
            elif jsonModel["Publication"] == "M2":
                jsonModel["Tag"] = np.arange(1, months[int(jsonModel["Ausgabe"]) * 2] + 1).tolist()
            elif jsonModel["Publication"] == "M":
                jsonModel["Tag"] = np.arange(1, months[int(jsonModel["Ausgabe"])] + 1).tolist()
            elif jsonModel["Publication"] == "M3":
                if int(jsonModel["Ausgabe"]) % 3 == 0:
                    jsonModel["Tag"] = np.arange(1, 10).tolist()
                elif int(jsonModel["Ausgabe"]) % 3 == 1:
                    jsonModel["Tag"] = np.arange(10, 20).tolist()
                else:
                    month = math.ceil(int(jsonModel["Ausgabe"]) / 3)
                    jsonModel["Tag"] = np.arange(20, months[month] + 1).tolist()
            elif jsonModel["Publication"] == "J":
                jsonModel["Tag"] = np.arange(1, 32).tolist()
            elif jsonModel["Publication"] == "J24":
                month = math.ceil(int(jsonModel["Ausgabe"]) / 2)
                if int(jsonModel["Ausgabe"]) % 2 == 1:
                    jsonModel["Tag"] = np.arange(1, 15).tolist()
                else:
                    jsonModel["Tag"] = np.arange(15, months[month] + 1).tolist()
            elif jsonModel["Publication"] == "HJ":
                jsonModel["Tag"] = np.arange(1, 32).tolist()
            elif jsonModel["Publication"] == "Q":
                jsonModel["Tag"] = np.arange(1, 32).tolist()
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
                    elif str(keyValue[0]).lower() == "zeitschrift":
                        jsonModel["ZEITSCHRIFTEN"].append(keyValue[-1])
                    elif keyValue[0].upper() == "QUELLE":
                        jsonModel["QUELLE"] = keyValue[-1]
                    else:
                        if keyValue[-1] not in jsonModel[keyValue[0].upper()]:
                            jsonModel[keyValue[0].upper()].append(keyValue[-1])
            f.write(json.dumps(jsonModel, ensure_ascii=False))
            if bool(mongodb_config_dict["JsonUpload"]):
                uploadJson(dict(jsonModel))
            if bool(cloudinary_config_dict["ImageUpload"]):
                publicId = jsonModel["Name"].replace(" ", "_") + "_" + str(jsonModel["Jahr"]) + "_" + jsonModel[
                    "Publication"].lower() + "_" + str(jsonModel["Ausgabe"])
                x = cloudinary.uploader.upload(ImageFolder + '/' + img,
                                               folder="images",
                                               public_id=publicId,
                                               overwrite=True,
                                               resource_type="image")
            ProgressBar['value'] += intervalLength
            window.update_idletasks()
            if count < len(AllImagesInInput):
                f.write(",")
            count += 1
        except Exception as e:
            error_count += 1
            f_error.write(img + " : " + str(e) + '\n')
            ProgressBar['value'] += intervalLength
            window.update_idletasks()
            count += 1
    f_error.close()
    f.write("]")
    f.close()
    if error_count == 0:
        status_image.config(image=greenImage)
    else:
        status_image.config(image=blueImage)
    main_label.config(text="Successfully created data for " + str(len(AllImagesInInput) - error_count) + " images out of " + str(len(AllImagesInInput)), bg="#A4A67C")


def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)


def open_settings_window():
    settings_window = Toplevel(window)
    settings_window.title("Einstellungen")
    settings_window.geometry("500x450")
    settings_window.configure(bg="#E5E5E5")

    settings_canvas = Canvas(
        settings_window,
        bg="#E5E5E5",
        height=450,
        width=500,
        bd=0,
        highlightthickness=0,
        relief="ridge"
    )
    settings_canvas.place(x=0, y=0)

    Label(settings_window, text="Cloudinary", font=("CircularStd Medium", 14), bg="#E5E5E5").place(x=50, y=30)

    cloudinary_cloud_name_entry = Entry(settings_window, bg="#FFFFFF", bd=0, highlightthickness=2, highlightbackground="#A4A772", highlightcolor="#A4A772",)
    cloudinary_cloud_name_entry.insert(0, cloudinary_config_dict['cloud_name'])
    cloudinary_cloud_name_entry.place(x=50, y=60, width=400, height=35)

    cloudinary_api_key_entry = Entry(settings_window, bg="#FFFFFF", bd=0, highlightthickness=2, highlightbackground="#A4A772", highlightcolor="#A4A772")
    cloudinary_api_key_entry.insert(0, cloudinary_config_dict['api_key'])
    cloudinary_api_key_entry.place(x=50, y=100, width=400, height=35)

    cloudinary_api_secret_entry = Entry(settings_window, bg="#FFFFFF", bd=0, highlightthickness=2, highlightbackground="#A4A772", highlightcolor="#A4A772")
    cloudinary_api_secret_entry.insert(0, cloudinary_config_dict['api_secret'])
    cloudinary_api_secret_entry.place(x=50, y=140, width=400, height=35)

    cloudinary_var = BooleanVar(value=cloudinary_config_dict['ImageUpload'])
    cloudinary_checkbox = Checkbutton(settings_window, text="Bilder hochladen", variable=cloudinary_var, bg="#E5E5E5")
    cloudinary_checkbox.place(x=50, y=180)

    Label(settings_window, text="MongoDB", font=("CircularStd Medium", 14), bg="#E5E5E5").place(x=50, y=220)

    mongodb_password_entry = Entry(settings_window, bg="#FFFFFF", bd=0, highlightthickness=2, highlightbackground="#A4A772", highlightcolor="#A4A772")
    mongodb_password_entry.insert(0, mongodb_config_dict['password'])
    mongodb_password_entry.place(x=50, y=250, width=400, height=35)

    mongodb_collection_entry = Entry(settings_window, bg="#FFFFFF", bd=0, highlightthickness=2, highlightbackground="#A4A772", highlightcolor="#A4A772")
    mongodb_collection_entry.insert(0, mongodb_config_dict['collection_name'])
    mongodb_collection_entry.place(x=50, y=290, width=400, height=35)

    mongodb_var = BooleanVar(value=mongodb_config_dict['JsonUpload'])
    mongodb_checkbox = Checkbutton(settings_window, text="JSON hochladen", variable=mongodb_var, bg="#E5E5E5")
    mongodb_checkbox.place(x=50, y=330)

    def save_settings():
        cloudinary_config_dict['cloud_name'] = cloudinary_cloud_name_entry.get()
        cloudinary_config_dict['api_key'] = cloudinary_api_key_entry.get()
        cloudinary_config_dict['api_secret'] = cloudinary_api_secret_entry.get()
        cloudinary_config_dict['ImageUpload'] = cloudinary_var.get()

        mongodb_config_dict['password'] = mongodb_password_entry.get()
        mongodb_config_dict['collection_name'] = mongodb_collection_entry.get()
        mongodb_config_dict['JsonUpload'] = mongodb_var.get()

        changeConfigValues()
        settings_window.destroy()

    save_button = Button(settings_window, text="Speichern", command=save_settings, bg="#A4A772", fg="#FFFFFF", bd=0, highlightthickness=0, relief="flat")
    save_button.place(x=200, y=400, width=100, height=30)

    settings_window.mainloop()

window = Tk()
window.title("BZS Image Tool V4.1.3")
# window.iconbitmap(relative_to_assets("Frame_16.ico"))
window.geometry("1000x800")
window.configure(bg="#E5E5E5")

canvas = Canvas(
    window,
    bg="#E5E5E5",
    height=800,
    width=1000,
    bd=0,
    highlightthickness=0,
    relief="ridge"
)

canvas.place(x=0, y=0)
image_image_1 = PhotoImage(
    file=relative_to_assets("image_1.png"))
image_1 = canvas.create_image(
    500.0,
    503.0,
    image=image_image_1
)

button_image_1 = PhotoImage(
    file=relative_to_assets("button_1.png"))
button_1 = Button(
    image=button_image_1,
    borderwidth=0,
    highlightthickness=0,
    command=findDuplicates,
    relief="flat",
)
button_1.place(
    x=393.0,
    y=542.0,
    width=208.0,
    height=54.0
)

button_image_2 = PhotoImage(
    file=relative_to_assets("button_2.png"))
button_2 = Button(
    image=button_image_2,
    borderwidth=0,
    highlightthickness=0,
    command=mainLoop,
    relief="flat",
    state="disabled"
)
button_2.place(
    x=393.0,
    y=476.0,
    width=208.0,
    height=54.0
)

button_image_3 = PhotoImage(
    file=relative_to_assets("button_3.png"))
button_3 = Button(
    image=button_image_3,
    borderwidth=0,
    highlightthickness=0,
    command=selectFolder,
    relief="flat",
)
button_3.place(
    x=393.0,
    y=410.0,
    width=208.0,
    height=54.0
)

sProgressBar = ttk.Style()
sProgressBar.theme_use('default')
sProgressBar.configure("grey.Horizontal.TProgressbar", foreground="#A4A772", background="#A4A772", borderwidth=1.2, relief="solid")
ProgressBar = ttk.Progressbar(mode='determinate', style="grey.Horizontal.TProgressbar")

ProgressBar.place(
    x=172.0,
    y=295.0,
    width=650.0,
    height=65.0
)

main_label = Label(text="Please select the image folder(*should only contain images in it)", font=("CircularStd Medium", -20), textvariable="")
main_label.config(bg="#D9D3D0", borderwidth=1.2, relief="solid", height=65, highlightthickness=0)
main_label.place(
    x=172.0,
    y=187.0,
    width=650.0,
    height=65.0
)

greenImage = ImageTk.PhotoImage(Image.open(relative_to_assets("1_green.png")))
blueImage = ImageTk.PhotoImage(Image.open(relative_to_assets("2_blue.png")))
redImage = ImageTk.PhotoImage(Image.open(relative_to_assets("3_red.png")))

status_image = Label(window, bg="#E5E5E5")
status_image.place(
    x=834.0,
    y=295.0,
    width=48.0,
    height=65.0
)

settings_label =  Button(window, text="Einstellungen", bg="#E5E5E5", font=("CircularStd Medium", -20), command=open_settings_window)
settings_label.place(
    x=734.87,
    y=667.85,
    width=132.6,
    height=20.66
)

checkedImg = PhotoImage(file=relative_to_assets("checkbox_selected.png"))
uncheckedImg = PhotoImage(file=relative_to_assets("checkbox_unselected.png"))

def changeMongo(x):
    if mongodb_config_dict['JsonUpload']:
        mongodb_config_dict['JsonUpload'] = False
        x.config(image=uncheckedImg)
    else:
        mongodb_config_dict['JsonUpload'] = True
        x.config(image=checkedImg)

def changeCloudinary(x):
    if cloudinary_config_dict['ImageUpload']:
        cloudinary_config_dict['ImageUpload'] = False
        x.config(image=uncheckedImg)
    else:
        cloudinary_config_dict['ImageUpload'] = True
        x.config(image=checkedImg)

mongo_button = Button(window, command=lambda: changeMongo(mongo_button), height=15, width=15)
cloudinary_button = Button(window, command=lambda: changeCloudinary(cloudinary_button), height=15, width=15)

if cloudinary_config_dict['ImageUpload']:
    cloudinary_button.config(image=checkedImg)
else:
    cloudinary_button.config(image=uncheckedImg)

if mongodb_config_dict['JsonUpload']:
    mongo_button.config(image=checkedImg)
else:
    mongo_button.config(image=uncheckedImg)

Label(window, text="Bilder hochladen", font=("CircularStd Medium", -20), bg="#E5E5E5").place(
    x=760.87,
    y=711.85,
    height=14.98,
    width=151.02
)

Label(window, text="Json hochladen", font=("CircularStd Medium", -20), bg="#E5E5E5").place(
    x=760.87,
    y=741.85,
    height=14.98,
    width=151.02
)

cloudinary_button.place(
    x=734.87,
    y=710.85
)

mongo_button.place(
    x=734.87,
    y=740.85
)

window.resizable(False, False)
window.mainloop()