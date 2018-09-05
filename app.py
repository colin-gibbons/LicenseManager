from flask import Flask, render_template, jsonify, abort, make_response, request
from urllib import request as urlRequest
from urllib import parse
from slackclient import SlackClient
import hashlib
import math
import json
import redis

app = Flask(__name__)
redis_ip = '35.229.39.79' #'redis'
redis_port = 6379

tasks = [ # list of available API commands
    {
        'id':'kv-record',
        'title': 'kv-record',
        'description': 'Records posted k/v pair to REDIS database.',
        'done':True
    },
    {
        'id':'search',
        'title': 'search',
        'description': 'Retrieves key value from REDIS database. ',
        'done':True
    }
]

@app.route('/') # render homepage
def home():
    return render_template('index.html')

@app.errorhandler(404) # handles 404 errors
def notFound(error):
    return make_response(jsonify({'error': '404: Page not found.'}), 404)

@app.route('/tasks', methods=['GET']) # displays list of available API commands
def get_tasks():
    return jsonify({'tasks': tasks})

@app.route('/<string:taskID>', methods=['GET'])  # returns info on a specific command
def getTask(taskID):
    task = [task for task in tasks if task['id'] == taskID]
    
    if len(task) == 0:
        abort(404)
    
    return jsonify({'task':task[0]})

@app.route('/search?query=<string:string>', methods=['GET']) # search database
def search(string):
    r = redis.StrictRedis(host=redis_ip, port=redis_port, db=0)
    out = r.get(string)
    error = 'none'

    if type(out) == bytes:
        out = out.decode("utf-8")
    else:
        out = False
        error = 'Key does not exist.1'

    return jsonify({'input':out, 'output':out, 'error': error})

@app.route('/search/<string:string>', methods=['GET']) # search database
def retrieve(string):
    r = redis.StrictRedis(host=redis_ip, port=redis_port, db=0)
    out = r.get(string)
    error = 'none'

    if type(out) == bytes:
        out = out.decode("utf-8")
    else:
        out = False
        error = 'Key does not exist.2'

    return jsonify({'input':string, 'output':out, 'error': error})

@app.route('/kv-record', methods=['POST', 'PUT']) # kv record
def record():
    data = request.form
    r = redis.StrictRedis(host=redis_ip, port=redis_port, db=0)
    error = 'none'
    if request.method == 'POST':
        for key, value in data.items():
            if not r.exists(key):
                r.set(key, value)
                print("Adding new k/v pair: (" + key + ", " + value +")")
            else:
                error = 'Unable to add pair: Key already exists.'
                return jsonify({'input':data, 'output':False, 'error': error})
    elif request.method == 'PUT':
        for key, value in data.items():
            if r.exists(key):
                r.set(key, value)
                print("Updating k/v pair: (" + key + ", " + value +")")
            else:
                error = 'Unable to update pair: Key does not exist.'
                return jsonify({'input':data, 'output':False, 'error': error})
    return jsonify({'input':data, 'output':True, 'error': error})

if __name__ == "__main__":
    app.run(host="0.0.0.0") 