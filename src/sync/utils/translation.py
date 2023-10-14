import requests


# 英語のラベルを日本語に変換する
def translate_to_japanese(text):
    url = 'https://script.google.com/a/m.cs.osakafu-u.ac.jp/macros/s/AKfycbzdJsOHmJWsylbyP6hColDLgzyozcI6LZ9Q1UhERg/exec'
    params = {
      'text': text,
      'source': 'en',
      'target': 'ja',
    }

    # よく出る単語は辞書に格納しておく
    examples = {
      'Computer keyboard': 'キーボード',
      'Computer monitor': 'モニター',
      'Television': 'モニター',
      'Mouse': 'マウス',
      'Laptop': 'ノートパソコン',
      'Mobile phone': '携帯電話',

      'Food': '食べ物',
      'Fruit': 'フルーツ',
      'Banana': 'バナナ',
      'Orange': 'オレンジ',
      'Apple': 'りんご',
      'broccoli': 'ブロッコリー',

      'Bottle': 'ペットボトル',
      'Bottled and jarred packaged goods': 'ペットボトル',
      'Drink': '飲み物',
      'Mug': 'マグカップ',

      'Furniture': '家具',
      'Cabinetry': 'キャビネット',
      'Desk': '机',
      'Table': 'テーブル',
      'Table top': 'テーブル',
      'Chair': '椅子',
      'Clock': '時計',
      'Whiteboard': 'ホワイトボード',
      'Home appliance': '家庭電化製品',
      'Microwave oven': '電子レンジ',
      'Lighting': 'ライト',
      'Sink': 'シンク',

      'Bag': 'バッグ',
      'Luggage & bags': 'バッグ',
      'Person': '人',
      'Clothing': '衣類',
      'Outerwear': 'アウター',
      'Pants': 'ズボン',
      'Shoe': '靴',
      'Glasses': '眼鏡',
      'Top': '上着',

      'Toy': 'おもちゃ',
      'Packaged goods': '包装品',

      'Ball': 'ボール',
      'Tennis ball': 'ボール',
    }

    if text in examples:
        print('{}: {}'.format(text, examples[text]))
        return examples[text]
    else:
        r = requests.get(url, params=params)
        print(r.text)

        if not r.status_code == 200:
            return text

        try:
            data = r.json()
            if data['code'] == 200:
                return data['text']
            else:
                return text
        except:
            return text
