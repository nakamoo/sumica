import sys
import base64
import requests


def get_wave(fname):
    with open(fname, "rb") as infile:
        return base64.b64encode(infile.read()).decode('ascii')


endpoint = "https://snowboy.kitt.ai/api/v1/train/"


############# MODIFY THE FOLLOWING #############
token = "65c4d0e0761454725c01e5cdf28046d07b268e49"
hotword_name = "???"
language = "jp"
age_group = ""
gender = ""
microphone = "macbook microphone"
############### END OF MODIFY ##################

if __name__ == "__main__":
    try:
        [_, wav1, wav2, wav3, out] = sys.argv
    except ValueError:
        print("Usage: %s wave_file1 wave_file2 wave_file3 out_model_name" % sys.argv[0])
        sys.exit()

    data = {
        "name": hotword_name,
        "language": language,
        #"age_group": age_group,
        #"gender": gender,
        "microphone": microphone,
        "token": token,
        "voice_samples": [
            {"wave": get_wave(wav1)},
            {"wave": get_wave(wav2)},
            {"wave": get_wave(wav3)}
        ]
    }

    response = requests.post(endpoint, json=data)
    if response.ok:
        with open(out, "wb") as outfile:
            outfile.write(response.content)
        print("Saved model to '%s'." % out)
    else:
        print("Request failed.")
        print(response.text)