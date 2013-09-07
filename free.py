from flask import Flask, request
import configparser
app = Flask(__name__)
config = configparser.ConfigParser()
config.read('config.ini')

env = config['dev']

app.debug = env.getboolean('debug')


@app.route('/')
def hello_world():
    return 'Hello World!'
@app.route('/make/')
def make():
    lat=request.args.get('lat')
    lon=request.args.get('lon') 

if __name__ == '__main__':
        app.run()
