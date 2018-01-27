import requests
from bs4 import BeautifulSoup

class Config:
    APP_NAME = "Easy Solver"
    APPID = "P656L2-X979UVXLJH" # YOUR ID
    API = "http://api.wolframalpha.com/v2/query?input={}&appid={}"

class Wolfram:
    def ask(query):
        print("Asking:", query)
        resp = requests.get(Config.API.format(query, Config.APPID))
        if resp.status_code != 200:
            return None
        dom = BeautifulSoup(resp.text, "lxml")
        result = dom.queryresult.findAll("pod", id="Solution")
        if result == []:
            result = dom.queryresult.findAll("pod", id="Result")
        if result == []:
            result = dom.queryresult.findAll("pod", id="ChemicalNamesFormulas:ChemicalData")
            
        subpods = result[0].findAll("subpod")
        return list(pod.plaintext.string for pod in subpods)   