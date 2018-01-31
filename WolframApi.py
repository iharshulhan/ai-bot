from collections import OrderedDict
import wolframalpha


class Config:
    APP_NAME = "Easy Solver"
    APPID = "P656L2-X979UVXLJH"  # YOUR ID
    API = "http://api.wolframalpha.com/v2/query?input={}&appid={}"


class Wolfram:
    @classmethod
    def ask(self, query):
        if not query:
            return "Write /solve command with your query.", None

        wolfram_query = " ".join(query)
        print("Asking:", wolfram_query)
        client = wolframalpha.Client(Config.APPID)
        respond = client.query(wolfram_query)

        if respond.success:
            try:
                result = []

                for pod in respond.pods:
                    if pod.id == "Plot" or \
                                    pod.id == "AlternativeForm" or \
                                    pod.id == "NumberLine" or \
                                    pod.id == "Illustration" or \
                                    pod.id == "VisualRepresentationOfTheIntegral":
                        for sub in pod.subpods:
                            if hasattr(sub, 'img'):
                                if pod.id == "NumberLine":
                                    result.append(("Number line", list(sub.img)[0].src))
                                elif pod.id == "VisualRepresentationOfTheIntegral":
                                    result.append(("Visual representation", list(sub.img)[0].src))
                                else:
                                    result.append((pod.id, list(sub.img)[0].src))
                try:
                    return next(respond.results).text, result
                except TypeError:
                    return None, result
            except Exception:
                return None, None

        else:
            return ":( Server is not responding. Try again later.", None
