from flask import Flask, request, send_from_directory
import configparser
import makemap
app = Flask(__name__)
config = configparser.ConfigParser()
config.read('config.ini')

env = config['dev']

app.debug = env.getboolean('debug')


@app.route('/')
def hello_world():
    return send_from_directory('static', 'index.html')

@app.route('/data/<path:filename>')
def download_file(filename):
	return send_from_directory('data',
                               filename, as_attachment=True)

@app.route('/make/')
def make():
    lat1=request.args.get('lat1')
    lon1=request.args.get('lon1')
    lat2=request.args.get('lat2')
    lon2=request.args.get('lon2')
    game=request.args.get('game')
    path = makemap.makemap(float(lat1), float(lon1), float(lat2), float(lon2), game=game)
    return path[1:]

if __name__ == '__main__':
        app.run()
