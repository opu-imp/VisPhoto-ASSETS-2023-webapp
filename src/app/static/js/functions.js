// main.js

window.onload = () => {
  // Radio buttons
  // const urlParams = location.serach;
  // console.log(urlParams);
  console.log(location.search);
  const params = new URLSearchParams(location.search);
  console.log(params.entries());
  for(var pair of params.entries()) {
   console.log(pair[0]+ ', '+ pair[1]);
  }


  // Speech Synthesis Utterance
  let choice = [];

  for (let i = 0; i < num_obj; i++) {
    document.getElementsByName('object' + i).forEach(element => {
      element.addEventListener('change', e => {
        console.log('object' + i + ': ' + e.target.value);
        const ul = e.target.parentNode.parentNode;
        const h2 = ul.previousElementSibling;

        if (e.target.value == '0' && e.target.checked) {
          choice.push(i);
        } else {
          choice = choice.filter(n => n!= i)
        }

        console.log(choice);
      });
    });
  }

  const sayCurrentSelection = () => {
    let text = '';
    if (choice.length == 0) {
      text = '何も選択されていません';
    } else {
      text = '選択中の物体は'
      choice.forEach(n => {
        const h3 = document.getElementById('object-name-' + n);
        const h2Clock = h3.parentNode.firstElementChild;
        const objectName = h3.innerText;
        const clockName = h2Clock.innerText;
        text += clockName + 'の' + objectName + ','
      });

      text += 'です'
    }

    console.log(text);

    const uttr = new SpeechSynthesisUtterance();
    uttr.text = text;
    uttr.lang = "ja-JP";
    speechSynthesis.speak(uttr);
  }

  Array.from(document.getElementsByClassName('utterance-button')).forEach(button => {
    button.onclick = sayCurrentSelection;
  })

  //
  // Speech recognition
  //
  const AudioContext = window.AudioContext || window.webkitAudioContext;
  const audioCtx = new AudioContext();

  const bufferSize = 4096;
  const sampleRate = audioCtx.sampleRate;
  const numChannels = 1;

  const audioData = [];
  let recLength = 0;
  let recording = false;

  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {

    navigator.mediaDevices.getUserMedia({
      audio: true,
      video: false
    }).then(stream => {

      audioCtx.resume();

      const source = audioCtx.createMediaStreamSource(stream);
      const node = audioCtx.createScriptProcessor(bufferSize, numChannels, numChannels);

      node.onaudioprocess = (e) => {
        if (!recording) return;

        for (let channel = 0; channel < numChannels; channel++) {
          const input = e.inputBuffer.getChannelData(channel);
          const bufferData = new Float32Array(input);
          audioData[channel].push(bufferData);
        }

        recLength += bufferSize;
      }

      source.connect(node);
      node.connect(audioCtx.destination);

      const mp3Files = {
        pppmp3: '/static/ppp.mp3',
        janmp3: '/static/jan.mp3',
        boomp3: '/static/boo.mp3',
      };

      const audioBuffers = {};
      const promiseArray = [];

      Object.keys(mp3Files).forEach((key) => {
        const promise = new Promise((resolve, reject) => {
          fetch(mp3Files[key]).then((response) => {
            if (!response.ok) {
              throw new Error();
            }
            return response.arrayBuffer();
          }).then((arrayBuffer) => {
            audioCtx.decodeAudioData(arrayBuffer, (audioBuffer) => {
              audioBuffers[key] = audioBuffer;
              resolve();
            });
          }).catch(() => {
            console.log('Failed to load ' + mp3Files[key]);
          });
        });

        promiseArray.push(promise);
      });

      // Promise.all(promiseArray).then(() => {
        const playSound = (key) => {
          const source = audioCtx.createBufferSource();
          source.buffer = audioBuffers[key];
          source.connect(audioCtx.destination);
          source.start(0);
          return source;
        }

        let timer = null;

        Array.from(document.getElementsByClassName('record-button')).forEach(button => {
          button.onclick = () => {
            if (!recording) {
              console.log('recording start');

              playSound('pppmp3');

              recording = true;

              for (let channel = 0; channel < numChannels; channel++) {
                audioData[channel] = [];
              }

              recLength = 0;

              setTimeout(() => {
                if (recording) {
                  timer = null;
                  button.click()
                }
              }, 10000);
            } else {
              console.log('recording stop');

              playSound('pppmp3');

              recording = false;

              clearTimeout(timer);

              const audioBlob = exportWAV(audioData);

              // const audio = document.createElement('audio');
              // audio.controls = true;
              // audio.src = URL.createObjectURL(audioBlob);
              //
              // const para = document.createElement('p');
              // para.innerText = 'result: ';
              //
              // const div = document.createElement('div');
              // div.appendChild(audio);
              // div.appendChild(para);

              // outputContainer = document.getElementById('output-container');
              // outputContainer.appendChild(div);

              recognize(audioBlob).then(text => {
                console.log(text);
                // para.innerText += text;

                  let flag = false;

                if (text == '切り取り') {
                  flag = true;
                  document.getElementById('submit-button').click()
                }

                for (let i = 0; i < num_obj; i++) {
                  const elementId = `object-name-${i}`
                  const h3 = document.getElementById(elementId);
                  console.log(h3.innerText);
                  if (h3.innerText == text) {
                    flag = true;

                    playSound('janmp3');

                    const jumpLink = button.nextElementSibling;
                    console.log(jumpLink);
                    const h2Clock = h3.parentNode.firstElementChild;
                    jumpLink.innerText = h2Clock.innerText +  'の' + text + 'へジャンプ';
                    jumpLink.href = location.href.split('#')[0] + '#' + elementId;
                    jumpLink.style.display = 'inline';
                    console.log(location.href.split('#')[0]);
                    break;
                  }
                }

                if (!flag) {
                  playSound('boomp3');
                }
              }).catch(error => {
                console.error(error);
              });
            }
          }
        });
      // });
    }).catch(error => {
      console.error(error);
    });

  }

  const mergeBuffers = (buffers) => {
    const result = new Float32Array(recLength);
    let offset = 0;
    for (let i = 0; i < buffers.length; i++) {
      result.set(buffers[i], offset);
      offset += buffers[i].length;
    }
    return result;
  }

  const interleave = (inputL, inputR) => {
    const length = inputL.length + inputR.length;
    const result = new Float32Array(length);

    let index = 0, inputIndex = 0;

    while (index < length) {
      result[index++] = inputL[inputIndex];
      result[index++] = inputR[inputIndex];
      inputIndex++;
    }

    return result;
  }

  const writeString = (view, offset, string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }

  const floatTo16BitPCM = (output, offset, input) => {
    for (let i = 0; i < input.length; i++, offset += 2) {
      const s = Math.max(-1, Math.min(1, input[i]));
      output.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
  }

  const encodeWAV = (samples) => {
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);

    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + samples.length * 2, true);
    writeString(view, 8, 'WAVE');
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, numChannels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * numChannels * 2, true);
    view.setUint16(32, numChannels * 2, true);
    view.setUint16(34, 16, true);
    writeString(view, 36, 'data');
    view.setUint32(40, samples.length * 2, true);
    floatTo16BitPCM(view, 44, samples);

    return view;
  }

  const exportWAV = (audioData) => {
    const buffers = [];
    for (let channel = 0; channel < numChannels; channel++) {
      buffers.push(mergeBuffers(audioData[channel]));
    }

    const samples = (numChannels === 2) ? interleave(buffers[0], buffers[1]) : buffers[0];
    const dataview = encodeWAV(samples);
    const audioBlob = new Blob([dataview], { type: 'audio/wav' });

    return audioBlob;
  }

  const convertArrayBufferToBase64 = (buffer) => {
    let binary = '';
    const bytes = new Float32Array(buffer);
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
  }

  const recognize = (audioBlob) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()

      reader.onload = () => {
        const result = new Uint8Array(reader.result)

        const data = {
          'config': {
            'encoding': 'LINEAR16',
            'languageCode': 'ja-JP'
          },
          'audio': {
            'content': convertArrayBufferToBase64(result)
          }
        }

        fetch('https://speech.googleapis.com/v1/speech:recognize?key=' + apiKey, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json; charset=utf-8'
          },
          body: JSON.stringify(data)
        }).then(response => {
          if (!response.ok) {
            throw new Error('Network response was not ok');
          }
          return response.json();
        }).then(data => {
          if (data.results) {
            resolve(data.results[0].alternatives[0].transcript);
          } else {
            resolve('');
          }
        }).catch(error => {
          reject(error);
        });
      }

      reader.readAsArrayBuffer(audioBlob);
    });
  }

}
