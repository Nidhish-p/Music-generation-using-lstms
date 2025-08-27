import os
import json
import music21 as m21
import numpy as np
import tensorflow.keras as keras # type: ignore
import warnings
warnings.filterwarnings('ignore')

KERN_DATASET_PATH = "D:/MusicGeneration/Music_generation/MgWebsite/dataset" # files from where we are loading our data
SAVE_DIR = "dataset" # where we are going to save our preprocessed data
SINGLE_FILE_DATASET = "file_dataset" # this will have our musical data in one unified format
MAPPING_PATH = "D:\MusicGeneration\Music_generation\MgWebsite\static\mapping.json" # this file will store the mapping of musical symbols to integers
SEQUENCE_LENGTH = 64 # this represents each i/p will be of 64 time steps i.e 64 notes or rests

# durations are expressed in quarter length
ACCEPTABLE_DURATIONS = [
    0.25, # 16th note
    0.5, # 8th note
    0.75,
    1.0, # quarter note
    1.5,
    2, # half note
    3,
    4 # whole note
]

def load_songs_in_kern(dataset_path):
    songs = []
    print(f"Looking for songs in: {dataset_path}")
    print(f"Path exists: {os.path.exists(dataset_path)}")
    
    # Check what files are actually there
    if os.path.exists(dataset_path):
        all_files = []
        for root, dirs, files in os.walk(dataset_path):
            all_files.extend(files)
        print(f"Total files found: {len(all_files)}")
        krn_files = [f for f in all_files if f.endswith('.krn')]
        print(f"Kern files found: {krn_files}")
    
    loaded_count = 0
    failed_count = 0
    
    for path, subdirs, files in os.walk(dataset_path):
        for file in files:
            # Better extension checking
            if file.endswith('.krn'):
                file_path = os.path.join(path, file)
                print(f"Attempting to load: {file}")
                
                try:
                    song = m21.converter.parse(file_path)
                    songs.append(song)
                    loaded_count += 1
                    print(f"✓ Successfully loaded: {file}")
                except Exception as e:
                    failed_count += 1
                    print(f"✗ Failed to load {file}: {str(e)}")
    
    print(f"Summary: {loaded_count} loaded, {failed_count} failed")
    return songs


def has_acceptable_durations(song, acceptable_durations):
    """Checks if all notes/rests have acceptable durations."""
    for note in song.flatten().notesAndRests:
        duration = note.duration.quarterLength
        print(f"Processing: {note} | Duration: {duration}")  # DEBUG
        
        if duration <= 0:  # Detect invalid negative durations
            print(f"Warning: Invalid negative duration {duration} in {note}")
            return False
        
        if duration not in acceptable_durations:
            print(f" Warning: Unacceptable duration {duration} found!")
            acceptable_durations.append(duration)
    return True



def transpose(song):
    """Transposes a song to C major or A minor, skipping problematic songs."""

    # Get the first part of the song
    parts = song.getElementsByClass(m21.stream.Part)
    
    if not parts:  
        print("⚠ Warning: No parts found in song. Skipping transposition.")
        return song  # Skip transposition, but continue processing

    measures_part0 = parts[0].getElementsByClass(m21.stream.Measure)
    
    if not measures_part0:  
        print("⚠ Warning: No measures found in first part. Skipping transposition.")
        return song  # Skip transposition, but continue processing

    # Search for key signature in the first measure
    key = None
    for element in measures_part0[0]:  
        if isinstance(element, m21.key.Key):
            key = element
            break  

    # If key signature is not found, estimate using music21
    if key is None:
        print("⚠ Warning: Key signature not found, skipping transposition.")
        return song

    # Ensure the key has a recognized mode before transposing
    if key.mode not in ["major", "minor"]:
        print(f"⚠ Warning: Unrecognized mode '{key.mode}', skipping transposition.")
        return song  # Skip transposition

    # Determine transposition interval
    interval = m21.interval.Interval(key.tonic, m21.pitch.Pitch("C" if key.mode == "major" else "A"))

    # Transpose the song
    transposed_song = song.transpose(interval)
    return transposed_song



def encode_song(song, time_step=0.25):
    """Converts a score into a time-series-like music representation. Each item in the encoded list represents 'min_duration'
    quarter lengths. The symbols used at each step are: integers for MIDI notes, 'r' for representing a rest, and '_'
    for representing notes/rests that are carried over into a new time step. Here's a sample encoding:

        ["r", "_", "60", "_", "_", "_", "72" "_"]

    :param song (m21 stream): Piece to encode
    :param time_step (float): Duration of each time step in quarter length
    :return:
    """

    encoded_song = []
    skipped_elements = 0
    unknown_types = set()

    for event in song.flatten().notesAndRests:
        try:
            symbol = None  # Initialize symbol

            # Handle notes
            if isinstance(event, m21.note.Note):
                symbol = event.pitch.midi  # Convert note to MIDI

            # Handle rests
            elif isinstance(event, m21.note.Rest):
                symbol = "r"

            # Handle chords: Convert each note in the chord (Polyphonic Approach)
            elif isinstance(event, m21.chord.Chord):
                for pitch in event.pitches:
                    symbol = pitch.midi  # Convert each note in the chord
                    
                    # Prevent Negative MIDI Values
                    if symbol < 0 or symbol > 127:
                        print(f"⚠ Warning: Invalid MIDI value {symbol}, skipping...")
                        continue
                    
                    encoded_song.append(symbol)  # Store each note separately
                continue  # Skip rest of loop since we handled this event

            # Handle unexpected cases
            else:
                unknown_types.add(type(event))  # Track unknown event type
                skipped_elements += 1
                continue  # Skip this event
            
            # Prevent Negative MIDI Values from being appended
            if isinstance(symbol, int) and (symbol < 0 or symbol > 127):
                print(f"⚠ Warning: Invalid MIDI value {symbol}, skipping...")
                continue  

            # Convert the note/rest into time-series notation
            steps = int(event.duration.quarterLength / time_step)
            for step in range(steps):
                if step == 0:
                    encoded_song.append(symbol)
                else:
                    encoded_song.append("_")

        except Exception as e:
            print(f"⚠ Error encoding element {event}: {e}")
            skipped_elements += 1
            continue  # Skip problematic elements

    if skipped_elements > 0:
        print(f"⚠ Skipped {skipped_elements} elements due to encoding errors.")
    if unknown_types:
        print(f"⚠ Unknown event types encountered: {unknown_types}")

    return " ".join(map(str, encoded_song))



def preprocess(dataset_path):

    # load songs
    print("Loading songs...")
    songs = load_songs_in_kern(dataset_path)
    print(f"Loaded {len(songs)} songs.")

    for i, song in enumerate(songs):

        # filter out songs that have non-acceptable durations
        if not has_acceptable_durations(song, ACCEPTABLE_DURATIONS):
            continue

        # transpose songs to Cmaj/Amin
        song = transpose(song)

        # encode songs with music time series representation
        encoded_song = encode_song(song)

        # save songs to text file
        save_path = os.path.join(SAVE_DIR, str(i))
        with open(save_path, "w") as fp:
            fp.write(encoded_song)


def load(file_path):
    with open(file_path, "r") as fp:
        song = fp.read()
    return song


def create_single_file_dataset(dataset_path, file_dataset_path, sequence_length):
    """Generates a file collating all the encoded songs and adding new piece delimiters.

    :param dataset_path (str): Path to folder containing the encoded songs
    :param file_dataset_path (str): Path to file for saving songs in single file
    :param sequence_length (int): # of time steps to be considered for training
    :return songs (str): String containing all songs in dataset + delimiters
    """

    new_song_delimiter = "/ " * sequence_length
    songs = ""

    # load encoded songs and add delimiters
    for path, _, files in os.walk(dataset_path):
        for file in files:
            file_path = os.path.join(path, file)
            song = load(file_path)
            songs = songs + song + " " + new_song_delimiter

    # remove empty space from last character of string
    songs = songs[:-1]

    # save string that contains all the dataset
    with open(file_dataset_path, "w") as fp:
        fp.write(songs)

    return songs


def create_mapping(songs, mapping_path):
    """Creates a json file that maps the symbols in the song dataset onto integers

    :param songs (str): String with all songs
    :param mapping_path (str): Path where to save mapping
    :return:
    """
    mappings = {}

    # identify the vocabulary
    songs = songs.split()
    vocabulary = list(set(songs))

    # create mappings
    for i, symbol in enumerate(vocabulary):
        mappings[symbol] = i

    # save voabulary to a json file
    with open(mapping_path, "w") as fp:
        json.dump(mappings, fp, indent=4)


def convert_songs_to_int(songs):
    int_songs = []

    # load mappings
    with open(MAPPING_PATH, "r") as fp:
        mappings = json.load(fp)

    # transform songs string to list
    songs = songs.split()

    # map songs to int
    for symbol in songs:
        int_songs.append(mappings[symbol])

    return int_songs


def generate_training_sequences(sequence_length):
    """Create input and output data samples for training. Each sample is a sequence.

    :param sequence_length (int): Length of each sequence. With a quantisation at 16th notes, 64 notes equates to 4 bars

    :return inputs (ndarray): Training inputs
    :return targets (ndarray): Training targets
    """

    # load songs and map them to int
    songs = load(SINGLE_FILE_DATASET)
    int_songs = convert_songs_to_int(songs)

    inputs = []
    targets = []

    # generate the training sequences
    num_sequences = len(int_songs) - sequence_length
    for i in range(num_sequences):
        inputs.append(int_songs[i:i+sequence_length])
        targets.append(int_songs[i+sequence_length])

    # one-hot encode the sequences
    vocabulary_size = len(set(int_songs))
    # inputs size: (# of sequences, sequence length, vocabulary size)
    inputs = keras.utils.to_categorical(inputs, num_classes=vocabulary_size)
    targets = np.array(targets)

    return inputs, targets


def main():
    preprocess(KERN_DATASET_PATH)
    songs = create_single_file_dataset(SAVE_DIR, SINGLE_FILE_DATASET, SEQUENCE_LENGTH)
    create_mapping(songs, MAPPING_PATH)
    inputs, targets = generate_training_sequences(SEQUENCE_LENGTH)

    print(inputs, targets)


if __name__ == "__main__":
    main()

