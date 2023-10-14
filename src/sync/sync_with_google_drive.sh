#! /bin/bash

# Usage
# sync_with_google_drive.sh visphoto01

readonly USER_NAME=$1
readonly SYNC_DIR="/uploads/"$1
readonly SAVE_DIR="/users/"$1

echo "USER_NAME: "${USER_NAME}
echo "SYNC_DIR:  "${SYNC_DIR}
echo "SAVE_DIR:  "${SAVE_DIR}

while true
do
  # ドライブと同期する
  rclone sync ${USER_NAME}:/ ${SYNC_DIR}/ --ignore-existing
  count=0

  # 同期した画像ファイルすべてに対して処理を行う
  for file in $(find ${SYNC_DIR}/ -maxdepth 1 -name *.JPG)
  do
    file_name=$(basename ${file} .JPG)
    echo ${file_name}

    # まだ検出処理がされていなければ処理を行う
    if [ ! -e ${SAVE_DIR}/${file_name} ]; then
      count=$(( count + 1 ))

      # ボイスメモも同期されていれば処理を行う
      if [ -e ${file%.JPG}.wav ]; then
        echo "start processing..."

        # 保存先のディレクトリを作成
        dst_path=${SAVE_DIR}/${file_name}
        mkdir -p ${dst_path}

        # 全方位画像をコピー
        cp ${file} ${dst_path}/theta.JPG

        # ボイスメモの処理
        cp ${file%.JPG}.wav ${dst_path}/audio.wav
        ffmpeg -i ${dst_path}/audio.wav -c:v copy -filter:a "volume=10.0" ${dst_path}/audio2.wav
        ffmpeg -i ${dst_path}/audio.wav -vn -ac 2 -ar 44100 -ab 256k -acodec libmp3lame -f mp3 ${dst_path}/audio.mp3

        # サムネイルを作成
        python generate_thumbnail.py ${file} ${dst_path} 800

        # 物体検出
        python erp_detection_gcp2.py ${file} ${dst_path}

        # 音声認識
        python speech_recognition.py ${dst_path}/audio2.wav ${dst_path}

        # 自動で切り取り
        python auto_crop.py ${dst_path}/theta.JPG ${dst_path}

        # データベースに登録
        python register_image.py ${dst_path}

      else
        echo "wav file has not been downloaded yet"
      fi
    else
      echo "already done"
    fi
  done

  if [ ${count} -eq 0 ]; then
    echo "count: zero"
    sleep 30
  else
    echo "count: non-zero"
  fi
done
