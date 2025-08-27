import tensorflow.keras as keras  # type: ignore
from .preprocessing import SEQUENCE_LENGTH, MAPPING_PATH
import json
import music21 as m21
import numpy as np
import os


class MelodyGenerator:
    def __init__(self, model_path="D:\\MusicGeneration\\Music_generation\\MgWebsite\\static\\model.h5"):
        self.model_path = model_path
        self.model = keras.models.load_model(model_path)

        with open(MAPPING_PATH, "rb") as fp:
            self._mappings = json.load(fp)
            
        # Debug: Check if "/" is in mappings
        print("Available mappings:", list(self._mappings.keys())[:20])  # First 20 keys
        print("'/' in mappings:", "/" in self._mappings)
        
        # Only use "/" if it exists in mappings, otherwise use a different start symbol
        if "/" in self._mappings:
            self._start_symbols = ["/"] * SEQUENCE_LENGTH
        else:
            # Use an existing symbol from your mappings, or empty
            self._start_symbols = []
            print("Warning: '/' not found in mappings, using empty start symbols")

    def generate_melody(self, seed, num_steps, max_seq_len, temperature):
        seed = seed.split()
        melody = seed
        print('melody:', melody)
        seed = self._start_symbols + seed
        print('seed:', seed)
        seed = [self._mappings[symbol] for symbol in seed]

        for _ in range(num_steps):
            seed = seed[-max_seq_len:]
            seed_onehot = keras.utils.to_categorical(seed, num_classes=len(self._mappings))
            seed_onehot = seed_onehot[np.newaxis, ...]

            probabilities = self.model.predict(seed_onehot)[0]
            output_int = self._sample_with_temperature(probabilities, temperature)

            seed.append(output_int)
            output_symbol = [k for k, v in self._mappings.items() if v == output_int][0]

            if output_symbol == "/":
                break

            melody.append(output_symbol)

        return melody

    def _sample_with_temperature(self, probabilities, temperature):
        predictions = np.log(probabilities) / temperature
        probabilities = np.exp(predictions) / np.sum(np.exp(predictions))

        choices = range(len(probabilities))
        index = np.random.choice(choices, p=probabilities)

        return index

    def save_melody(self, melody, step_duration=1, format="midi", midi_filename="melody.mid"):
        stream = m21.stream.Stream()
        start_symbol = None
        step_counter = 1

        for i, symbol in enumerate(melody):
            if symbol != "_" or i + 1 == len(melody):
                if start_symbol is not None:
                    quarter_length_duration = step_duration * step_counter
                    if start_symbol == "r":
                        m21_event = m21.note.Rest(quarterLength=quarter_length_duration)
                    else:
                        m21_event = m21.note.Note(int(start_symbol), quarterLength=quarter_length_duration)

                    stream.append(m21_event)
                    step_counter = 1

                start_symbol = symbol
            else:
                step_counter += 1

        stream.write(format, midi_filename)
        print(f"✅ MIDI file saved as: {midi_filename}")
        
        return midi_filename
