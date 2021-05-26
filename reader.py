# Python libraries
import re
import os
import datetime
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import csv

class ImageMeta:
    @staticmethod
    def __checkifileexist(filepath):
        if os.path.isfile(filepath):
            pass
        else:
            raise ValueError("No file found with path {}".format(filepath))
    
    @staticmethod
    def __get_exif(filename):
        """
        Function to read exif data from the image file
        """
        image = Image.open(filename)
        image.verify()
        return image._getexif()

    @staticmethod
    def __get_geotagging(exif):
        """
        Function to get the GPS info from the Exif data
        """
        if not exif:
            raise ValueError("No EXIF metadata found")
        geotagging = {}
        for (idx, tag) in TAGS.items():
            if tag == 'GPSInfo':
                if idx not in exif:
                    raise ValueError("No EXIF geotagging found")

                for (key, val) in GPSTAGS.items():
                    if key in exif[idx]:
                        geotagging[val] = exif[idx][key]
        return geotagging

    @staticmethod
    def __get_decimal_from_dms(dms, ref) -> float:
        """
        Function to convert the degree.min.sec GPS data to degrees

        INPUT:
            dms(tuple):     Tuple from the exif geotags
            ref(str):       Location reference for the GPS tag
            
        RETURN
            <float>
            Returns floating point value of the location.
        """
        degrees = dms[0][0] / dms[0][1]
        minutes = dms[1][0] / dms[1][1] / 60.0
        seconds = dms[2][0] / dms[2][1] / 3600.0
        if ref in ['S', 'W']:
            degrees = -degrees
            minutes = -minutes
            seconds = -seconds
        return round(degrees + minutes + seconds, 6)

    
    @classmethod
    def readfromimage(cls, filename:str) -> dict:
        """
            Function to read EXIF Meta data from a an image

        INPUT:
            filename(str):  Full file path of the image to read

        RETURN:
            <dict>
            Returns a dict with 
                datetime:       DateTime for the image taken
                framewidth:     Width of the image
                frameheight:    Height of the image
                focallength:    Focal lenght of the camera
                lat:            GPS laitude of the camera when image was taken
                lng:            GPS longitude of the camera when image was taken
                heading:        GPS heading of he camera from True North. Measurement from mobile compas.
                altitude:       GPS altitude above sea level in meters
                yaw:            Yaw angle of the camera from True North. Measurement from mobile compas.
                pitch:          Mobile pitch angle from orintation sensor.
                roll:           Mobile roll angle from orintation sensor.
                senwidth:       Camera sensor array width.
                senheight:      Camera sensor array height.
                h_fov:          Horizontal field of view for the camera in potrait mode.
        """
        # Check if the file exits
        cls.__checkifileexist(filename)

        # Read image and load exif data
        exif = cls.__get_exif(filename)
        # Get labels for each entry in data
        labeled_exif = {}
        for (key, val) in exif.items():
            labeled_exif[TAGS.get(key)] = val

        # Get Geographic metadata
        geotags = cls.__get_geotagging(exif)
        # print(int.from_bytes(geotags["GPSAltitudeRef"], byteorder="little"))
        
        # Capture only few data and return as a dict
        ret = dict()
        ret["datetime"]    = labeled_exif["DateTimeOriginal"]
        ret["imgwidth"]    = labeled_exif["ImageWidth"]
        ret["imgheight"]   = labeled_exif["ImageLength"]
        ret["focallength"] = labeled_exif["FocalLength"][0]/labeled_exif["FocalLength"][1]
        ret["lat"]         = cls.__get_decimal_from_dms(geotags["GPSLatitude"], geotags["GPSLatitudeRef"])
        ret["lng"]         = cls.__get_decimal_from_dms(geotags["GPSLongitude"], geotags["GPSLongitudeRef"])
        ret["heading"]     = geotags["GPSImgDirection"][0]/geotags["GPSImgDirection"][1]
        ret["altitude"]    = geotags["GPSAltitude"][0]/geotags["GPSAltitude"][1]

        # Get Yaw, pitch and roll
        split_string = re.split("[\x00^:,]", labeled_exif["UserComment"])
        ret["yaw"]   = float(split_string[4])
        ret["pitch"] = float(split_string[6])
        ret["roll"]  = float(split_string[8])

        # Camera Sensor length/width
        # These values are hard-coded for Samsung SM-A505F mobiles
        if (labeled_exif["Make"].lower() == "samsung") and labeled_exif["Model"].lower() == "sm-a505f":
            ret["senwidth"]  = 5.18 # millimeters
            ret["senheight"] = 3.89 # millimeters
            ret["h_fov"]     = 66.8 # degrees - Field of view

        return ret
    
    @classmethod
    def readfrombatch(cls, listofimg:list, csvwrite=False):
        """
         Function to read exif data from given list of image path.
         The function saves all the data into a csv in the same location as the script.

         INPUT:
            listofimg(list):    List of image
            csvwrite(bool):     Flag to create a csv file
        """
        print("[INFO] Reading EXIF data, ", end=" ")
        metaData = list()
        for filepath in listofimg:
            # Check if the file exits
            cls.__checkifileexist(filepath)
            meta = cls.readfromimage(filepath)
            meta["imgname"] = os.path.basename(filepath)
            metaData.append(meta)
        print("Done!")

        if csvwrite:
            # Write to csv
            print("[INFO] Saving to csv, ", end=" ")
            csv_columns = ['datetime','imgwidth','imgheight', 'focallength',\
                        'lat', 'lng', 'heading', 'altitude', 'yaw', 'pitch', 'roll', 'senwidth', 'senheight', 'h_fov', 'imgname']
            csv_file = "metaData-images.csv"
            
            while True:
                try:
                    with open(csv_file, 'w') as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
                        writer.writeheader()
                        for data in metaData:
                            writer.writerow(data)
                    print("Done!")
                    print("CSV saved as ", csv_file)
                    break
                except IOError:
                    input("Could not open file! Please close Excel. Press Enter to retry.")
        return metaData


class VideoMeta:
    def __init__(self, ):
        pass

    @staticmethod
    def __checkifileexist(filepath):
        if os.path.isfile(filepath):
            pass
        else:
            raise ValueError("No file found with path {}".format(filepath))

    @classmethod
    def readfromsrt(cls, srtfilepath:str, csvwrite=False):
        """Function to read the meta data from OpenCamera .srt files 
        with following data
                datetime:       DateTime for the image taken
                lat:            GPS laitude of the camera when image was taken
                lng:            GPS longitude of the camera when image was taken
                heading:        GPS heading of he camera from True North. Measurement from mobile compas.
                altitude:       GPS altitude above sea level in meters
                start_time: Start time of the data acq for video
                end_time:   Start time of the data acq for video

        INPUT:
            srtfilepath(str):  Path for .srt file to read. 
            csvwrite(bool):    Flag to create a csv file
        """
        metaData = list()
        # Check if the file exits
        cls.__checkifileexist(srtfilepath)

        # Reading the file
        print("[INFO] Reading .srt data, ", end=" ")
        with open(srtfilepath, "r") as f:
            data = f.readlines()

        counter = 1
        for itr, line in enumerate(data):
            try:
                if int(line) == counter:
                    counter += 1
                    loc    = re.split('[°\'\"\,\ ]', data[itr+3])
                    s_time = data[itr+1].split("-->")[0].split(" ")[0]
                    e_time = data[itr+1].split("-->")[1].split("\n")[0] 

                    ret = dict()
                    ret["datetime"]    = data[itr+2].split("\n")[0]
                    ret["lat"]         = round(float(int(loc[:3][0]) + int(loc[:3][1])/60 + int(loc[:3][2])/3600), 6)
                    ret["lng"]         = round(float(int(loc[5:8][0]) + int(loc[5:8][1])/60 + int(loc[5:8][2])/3600), 6)
                    ret["heading"]     = float(loc[12])
                    ret["altitude"]    = float(loc[10].split("m")[0])
                    ret["frame_start"] = datetime.datetime.strptime(s_time, "%H:%M:%S,%f")
                    ret["frame_end"]   = datetime.datetime.strptime(e_time, " %H:%M:%S,%f")
                    metaData.append(ret)
            except ValueError as e:
                pass
        print("Done!")
        
        if csvwrite:
            # Write to csv
            print("saving to csv, ", end=" ")
            csv_columns = ['datetime', 'lat', 'lng', 'heading', 'altitude', 'frame_start', 'frame_end']
            csv_file = "metaData-{}.csv".format(os.path.basename(srtfilepath).split(".")[0])
            
            while True:
                try:
                    with open(csv_file, 'w') as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
                        writer.writeheader()
                        for data in metaData:
                            writer.writerow(data)
                    print("Done!")
                    print("CSV saved as ", csv_file)
                    break
                except IOError:
                    input("Could not open file! Please close Excel. Press Enter to retry.")

        return metaData



if __name__ == "__main__":

    # ############################
    # # Reading Meta from Images #
    # ############################
    # image_file_path = "images/image (1).jpg"
    # # # Read meta for the image
    # print(ImageMeta.readfromimage(image_file_path))

    # # Read meta from batch of images and save as csv
    # folderPath = "images/"
    # image_path_list = [os.path.join(folderPath, filename) for filename in os.listdir(folderPath)]
    # data = ImageMeta.readfrombatch(image_path_list)
    # for line in data:
    #     print(line)
    #     print(" ")

    ############################
    # Reading Meta from videos #
    ############################
    filename = "videos/VID_20210520_105150.srt"
    data = VideoMeta.readfromsrt(filename, csvwrite=True)
    for line in data:
        print(line)
        print("")

    
    
    