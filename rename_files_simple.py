from os import listdir, rename, path
from os.path import isfile, join
from datetime import datetime

class Rename:
    def __init__(self):
        self.already_renamed = []

    # rename file based on first word of the phrase, line number, and the timestamp
    def rename_file(self, phrase, folder, extension, line_num):

        # get the filenames that you want to rename - currently gets all the files in the specified directory
        # it should now be ignoring all hidden files
        # HAS FILE NAMES - NOT FILE PATHS
        self.file_names = sorted(
            [f for f in listdir(folder) if isfile(join(folder, f)) and not f.startswith('.') and f not in self.already_renamed],
            key=lambda f: path.getmtime(join(folder, f))
        )

        diphone = phrase.replace(" ", "")
        time_format = '%m%d%H%M%S'
        time_stamp = datetime.now().strftime(time_format) # month, day, hour, minute, second
        old_file_path = path.join(folder, self.file_names[0])
        new_file_name = f"{line_num}_{diphone}_{time_stamp}.{extension}"
        new_file_path = path.join(folder, new_file_name)

        rename(old_file_path, new_file_path)

        print(old_file_path, " renamed to ", new_file_path)


        # ADDING THE FILE NAME SO WE CAN COMPARE AND SEE IF IT'S ALREADY RENAMED
        self.already_renamed.append(new_file_name)

        # Update the list of files after renaming
        self.file_names = sorted(
            [f for f in listdir(folder) if isfile(join(folder, f)) and not f.startswith('.') and f not in self.already_renamed],
            key=lambda f: path.getmtime(join(folder, f))
        )

    def reset(self):
        self.already_renamed = []  