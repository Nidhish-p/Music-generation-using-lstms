from django.shortcuts import render
from django.http import JsonResponse
from .Melody_generator import MelodyGenerator
import os
from django.templatetags.static import static
# Create your views here.

def index(request):
    return render(request,'index.html')

def mg(request):
    if request.method == "POST":
        sample_no = request.POST.get("sample_no") 
        dataset = r"D:\MusicGeneration\Music_generation\MgWebsite\dataset"
        print('sample:', sample_no)

        seed_path = os.path.join(dataset, sample_no)
        with open(seed_path, 'r') as f:
            seed = f.read(200)

        print(f"Contents of file {sample_no}:\n{seed}")
        num_steps = 250
        max_seq_len = 20  
        temperature = 1.7

        mg = MelodyGenerator()
        melody = mg.generate_melody(seed, num_steps, max_seq_len, temperature)

        midi_filename = "generated_melody.midi"
        midi_path = os.path.join("static", midi_filename)

        print('✅ Model ran successfully!')

        # Save MIDI file
        mg.save_melody(melody, midi_filename=midi_path)
        midi_file_url = static("generated_melody.midi")
        return render(request,'generate.html',{'midi_file':midi_file_url})

    return render(request, 'generate.html')