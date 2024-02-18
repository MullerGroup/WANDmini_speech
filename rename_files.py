from os import listdir, rename, path
from os.path import isfile, join

class Rename:

    def __init__(self):
        self.file_path = './utterances.txt'
        self.word_list = self.extract_phrases()
        self.utterances = {}
        self.count_utterances()
        self.data_path = "data"

        # get the filenames that you want to rename - currently gets all the files in the /test directory
        self.file_names = [f for f in sorted(listdir(self.data_path)) if isfile(join(self.data_path, f))]

        # removes the viz_data.m file -> that shouldn't be renamed
        self.file_names.remove("viz_data.m")

    # extract words from utterance list
    def extract_phrases(self):
        try:
            with open(self.file_path, 'r') as file:
                phrases = [line.strip() for line in file if line.strip()]
            return phrases
        except FileNotFoundError:
            print(f"The file at {self.file_path} was not found.")
            return []
        except Exception as e:
            print(f"An error occurred: {e}")
            return []

    # add each unique word into a dictionary 
    def count_utterances(self):
        for i in self.word_list:
            if i not in self.utterances:
                self.utterances[i] = 1

    # rename each file based on the word and the occurences 
    def rename_files(self):
        for i in range(len(self.file_names)):
            curr_word = self.word_list[i]
            occurence = self.utterances[curr_word]
            old_filename = path.join(self.data_path, self.file_names[i])
            new_filename = path.join(self.data_path, f"{curr_word}_{occurence}.mat")
            rename(old_filename, new_filename)
            self.utterances[curr_word] = occurence + 1