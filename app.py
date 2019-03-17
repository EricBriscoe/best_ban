from flask import Flask
import configparser
import requests

app = Flask(__name__)
config = configparser.ConfigParser()
config.read("config.ini")


@app.route("/")
def hello_world():
    return "Hello World!"


if __name__ == "__main__":
    app.run()
