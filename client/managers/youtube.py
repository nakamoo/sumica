import time
import subprocess

class Manager:
    def __init__(self, server_ip):
        pass

    def start(self):
        while True:
            command = "chrome-cli list links | grep www.youtube.com"
            proc = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout_data, stderr_data = proc.communicate()
            links = stdout_data.decode('ascii')

            if not links == '':
                while True:
                    start = links.find('http')
                    end = links.find('\n')
                    if (start != -1) and (end != -1):
                        link = links[start: end]
                        data = {}
                        data["time"] = datetime.datetime.utcfromtimestamp(time.time())
                        data['app'] = "youtube"
                        data['link'] = link
                        print(data)
                        #db.save_youtube_data(data)
                        links = links[end + 1:]
                    else:
                        break

            time.sleep(10)