from flask import Flask, render_template, jsonify, abort, make_response, request
from urllib import request as urlRequest
from urllib import parse
import math
import json
import boto3
import decimal
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

app = Flask(__name__)
dynamo_url = 'http://localhost:8000' #'redis'

dynamodb = boto3.resource('dynamodb', region_name='us-west-2', endpoint_url=dynamo_url)

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

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

@app.route('/') # render homepage
def home():
    return render_template('index.html')

@app.route('/search', methods=['GET']) # search database
def search():
    string = request.args.get('query')

    table = dynamodb.Table("Link")

    try:
        response = table.get_item(
            Key={
                'userID': string
            }
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
        return render_template('noResultsFound.html', name=string)
    else:
        item = response['Item']
        print("GetItem succeeded:")
        print(json.dumps(item, indent=4, cls=DecimalEncoder))
        name = item['userID']
        software = item['software']

        # TODO: generate special keys for each software to more securely delete (md5 user/software/salt)
        # TODO: redirect to /user/userID
        return render_template('user.html', userID=name, software=software)

@app.route('/user/<string:userID>/<string:softwareID>', methods=['DELETE'])
def deleteLicense(userID, softwareID):
    table = dynamodb.Table("Link")
    response = table.update_item(
        Key={
            'userID': userID
        },
        UpdateExpression="$unset software." + softwareID,
        ReturnValues="UPDATED_NEW"
    )

    print("delete item succeeded:")
    print(json.dumps(response, indent=4, cls=DecimalEncoder))

@app.route('/user/<string:userID>', methods=['GET'])
def getUser(userID):
    return render_template('index.html')

@app.route('/kv-record', methods=['POST', 'PUT']) # kv record
def record():
    data = request.form
    return jsonify({'input':data, 'output':True, 'error': "error"})

@app.errorhandler(404) # handles 404 errors
def notFound(error):
    return make_response(jsonify({'error': '404: Page not found.'}), 404)

@app.route('/tasks', methods=['GET']) # displays list of available API commands
def getTasks():
    return jsonify({'tasks': tasks})

@app.route('/<string:taskID>', methods=['GET'])  # returns info on a specific command
def getTask(taskID):
    task = [task for task in tasks if task['id'] == taskID]
    
    if len(task) == 0:
        abort(404)
    
    return jsonify({'task':task[0]})

if __name__ == "__main__":
    app.run(host="0.0.0.0") 