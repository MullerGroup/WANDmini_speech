Fixed a bug in the start_stop_experiment() method -> made it start from the first word (all over again). Before this if you used to start the experiment after stopping, it would start it from whatever word you stopped at.

Instead of calling the start_stop_experiment() method at state 4, the program now calls the next_word() method if there are more words left to display

This method starts streaming and sends the state back to state 1

Removed debug statements describing current state

Changes to color
- Gray when countdown is going on
- Green when the word is showing
- Green when the experiment is completed and “Done” pops up

Increased size of text cues
Made full screen toggleable and increased the size of the window

Wrote the script to rename files - called from start_stop_experiment()
- Since files are ordered based on the date and time, it sorts the files numerically in ascending order, and renames the files with the word and a counter
- Goes through each file in the data directory, and matches it up with the utterance list (the first file becomes heed_1, the second one becomes kale_1, and so on)
- Even if the words are in a different order (eg. kale, heed, kale) it is able to correctly rename them as it keeps track of the count
- However, we will need to ensure that the directory it is reading files from is empty before the script is run, so that it only renames files that are new. It behaves strangely if there are files already in the directory (apart from viz_data.m, since this will not be renamed)
- Also, if we are resetting the experiment and want to record data again, we will need to ensure the data directory is empty.