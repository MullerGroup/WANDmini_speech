from os import listdir, rename, path
from os.path import isfile, join
from datetime import datetime

class Rename:
    def __init__(self):
        self.already_renamed = []

    # rename file based on first word of the phrase, and the timestamp
    def rename_file(self, phrase, folder, extension):

        # get the filenames that you want to rename - currently gets all the files in the specified directory
        # it should now be ignoring all hidden files
        self.file_names = [f for f in sorted(listdir(folder)) if isfile(join(folder, f)) and not f.startswith('.') and f not in self.already_renamed]

        first_word = phrase.split()[0]
        time_stamp = datetime.now().strftime('%m%d%H%M%S') # month, day, hour, minute, second
        old_filename = path.join(folder, self.file_names[0])
        new_filename = path.join(folder, f"{first_word}_{time_stamp}.{extension}")
        rename(old_filename, new_filename)
        self.already_renamed.append(new_filename)