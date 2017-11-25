## info
* pip install SpeechRecognition
* pip install PyAudio
* hotword detection requires Snowboy by kitt.ai
 * directory "snowboy" should be in same folder as HAI
* speech recognition (jp) uses Google Speech Recognition
* speech recognition requires hotword detection
* hotword detectionには今はスクリプトで個人用音声データの作成（.pmdl）が必要（既存のファイルは野口の声に特化している）
1. managers/hotword/register.pyで３つのwavファイルを作成
2. managers/hotword/get_pmdl.py 0.wav 1.wav 2.wav <ask,no, or yes>.pmdlでpmdlを作成
3. pmdlをclient/hotwords/に入れる
音声の例：ask=「ねえ」，no=「いっ」，yes=「うん」
