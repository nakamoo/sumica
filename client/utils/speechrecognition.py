import speech_recognition as sr 

def confirm():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
    try:
        text = r.recognize_google(audio, language="ja")
        print(text)
    except sr.UnknownValueError:
        print("Sphinx could not understand audio")
        return None
    except sr.RequestError as e:
        print("Sphinx error; {0}".format(e))
        return None

    if text == "はい":
        return True
    elif text == "いいえ":
        return False

    return None

if __name__ == "__main__":
    confirm()
