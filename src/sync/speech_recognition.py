import base64
import io
import json
import os
import sys

from google.cloud import speech
import MeCab


if __name__ == '__main__':
    args = sys.argv
    input_path = args[1]
    output_dir = args[2]

    client = speech.SpeechClient()

    with io.open(input_path, 'rb') as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        # sample_rate_hertz=16000,
        language_code='ja-JP',
    )

    response = client.recognize(config=config, audio=audio)

    for result in response.results:
        print('Transcript: {}'.format(result.alternatives[0].transcript))

    transcript = ''

    if response.results:
        transcript = response.results[0].alternatives[0].transcript

    m = MeCab.Tagger("-d /var/lib/mecab/dic/ipadic-utf8 -O chasen")
    nouns = [line.split()[0] for line in m.parse(transcript).splitlines() if "名詞" in line.split()[-1]]

    with open(os.path.join(output_dir, 'objects.json'), mode='r') as f:
        objects = json.load(f)

    objects['transcript'] = transcript
    objects['nouns'] = nouns

    with open(os.path.join(output_dir, 'objects.json'), mode='w') as f:
        json.dump(objects, f, indent=2, ensure_ascii=False)
