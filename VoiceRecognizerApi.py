import operator
import os
import tempfile
import requests
import subprocess
from bs4 import BeautifulSoup
import Config


class VoiceRecognizer:
    def ask(data, length, uid, lang="auto"):
        url = "https://asr.yandex.net/asr_xml?uuid={}&key={}&topic={}&lang={}&disableAntimat={}"
        url = url.format(uid, Config.yandex_api, "queries", lang, "true")
        headers = {"Content-Type": "audio/x-pcm;bit=16;rate=16000", "Content-Length": str(length)}
        resp = requests.post(url, data=data, headers=headers)
        dom = BeautifulSoup(resp.text, "html5lib")
        result = dict(
            (var.string, float(var["confidence"])) for var in dom.html.body.recognitionresults.findAll("variant"))

        res1 = max(result.items(), key=operator.itemgetter(1))

        url = "https://asr.yandex.net/asr_xml?uuid={}&key={}&topic={}&lang={}&disableAntimat={}"
        url = url.format(uid, Config.yandex_api, "queries", 'en', "true")
        headers = {"Content-Type": "audio/x-pcm;bit=16;rate=16000", "Content-Length": str(length)}
        resp = requests.post(url, data=data, headers=headers)
        dom = BeautifulSoup(resp.text, "html5lib")
        result = dict(
            (var.string, float(var["confidence"])) for var in dom.html.body.recognitionresults.findAll("variant"))

        res2 = max(result.items(), key=operator.itemgetter(1))

        url = "https://asr.yandex.net/asr_xml?uuid={}&key={}&topic={}&lang={}&disableAntimat={}"
        url = url.format(uid, Config.yandex_api, "queries", 'ru', "true")
        headers = {"Content-Type": "audio/x-pcm;bit=16;rate=16000", "Content-Length": str(length)}
        resp = requests.post(url, data=data, headers=headers)
        dom = BeautifulSoup(resp.text, "html5lib")
        result = dict(
            (var.string, float(var["confidence"])) for var in dom.html.body.recognitionresults.findAll("variant"))

        res3 = max(result.items(), key=operator.itemgetter(1))

        # print(res1, res2, res3)
        return max(res1, res2, res3)[0]

    def ogg2pcm(ogg):
        with tempfile.TemporaryFile() as temp_out:
            name_in = None

            if ogg:
                temp_in = tempfile.NamedTemporaryFile(delete=False)
                temp_in.write(ogg)
                name_in = temp_in.name
                temp_in.close()

            command = [
                "ffmpeg",
                "-i", name_in,
                '-f', 's16le',
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-'
            ]

            process = subprocess.Popen(command, stdout=temp_out, stderr=subprocess.DEVNULL)
            process.wait()
            os.remove(name_in)
            temp_out.seek(0)

            return temp_out.read()
