from flask import *
from flask import Flask, jsonify, request, Response
from flask_pymongo import PyMongo
from bson import json_util
from bson.objectid import ObjectId
import json
from firebase_admin import credentials, firestore, initialize_app

from werkzeug.security import generate_password_hash, check_password_hash
import pyrebase
#pip install -U Werkzeug  #Esta librería se usa para cifrar contraseñas
#pip install Flask-PyMongo
#pip install firebase_admin
#pip install pyrebase

#Firebase auth
#Write your api keys and data here.
config = {
    "apiKey": "",
    "authDomain": "",
    "databaseURL": "",
    "projectId": "",
    "storageBucket": "",
    "messagingSenderId": "",
    "appId": ""
}

firebase = pyrebase.initialize_app(config)

auth = firebase.auth()


app = Flask(__name__)
app.secret_key = 'myawesomesecretkey'

app.config['MONGO_URI'] = 'mongodb://localhost:27017/myDatabase'

mongo = PyMongo(app)


# Initialize Firestore DB
cred = credentials.Certificate('key.json')
default_app = initialize_app(cred)
db = firestore.client()
todo_ref = db.collection('users')

#Method for syncing to firestore.
def syncToFirestore():
    #We obtain the users from our local Mongo DB that have not being sent to Firestore yet.
    #The flag isSynced=False indicates that a user is not yet replicated on Firestore.
    users = mongo.db.users.find({ 'isSynced': False })
    
    #We loop over those users and we sent them to Firestore.
    for user in users:            
        doc_ref = db.collection('users').document(str(user["_id"]))
        doc_ref.set({
            'username' : user["username"],
            'email': user["email"],
            'password': user["password"]
        })


@app.route('/users', methods=['POST'])
def createUser():
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']

    if (username and email and password):
        passHashed = generate_password_hash(password)
        #We create the user with flag isSynced=False, this way when the sync process runs, it will
        #detect all users that have note been sent to Firestore and it will send them to Firestore.
        id = mongo.db.users.insert_one(
            {'username': username, 'email': email, 'password': passHashed, 'isSynced':False})
        response = jsonify({
            '_id': str(id),
            'username': username,
            'email': email,
            'password': password            
        })
        #Since the request resulted in a new resource creaated, the Status Code = 201.
        response.status_code = 201
        syncToFirestore()
        return response
    else:
        return notFound()


@app.route('/users', methods=['GET'])
def getUsers():
    #We retrieve all users from Mongo DB.
    users = mongo.db.users.find()
    response = json_util.dumps(users)
    return Response(response, mimetype="application/json")

#Retrieve a user by id. 
@app.route('/users/<id>', methods=['GET'])
def getUser(id):
    print(id)
    user = mongo.db.users.find_one({'_id': ObjectId(id), })
    response = json_util.dumps(user)
    return Response(response, mimetype="application/json")


@app.route('/users/<id>', methods=['DELETE'])
def deleteUser(id):
    mongo.db.users.delete_one({'_id': ObjectId(id)})
    response = jsonify({'message': 'The user with Id ' + id + ' has been deleted'})
    response.status_code = 200

    db.collection('users').document(str(id)).delete()

    return response


@app.route('/users/<_id>', methods=['PUT'])
def updateUser(_id):
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']
    if (username and email and password and _id):
        passHashed = generate_password_hash(password)
        mongo.db.users.update_one(
            {'_id': ObjectId(_id['$oid']) if '$oid' in _id else ObjectId(_id)}, {'$set': {'username': username, 'email': email, 'password': passHashed}})
        response = jsonify({'message': 'The user with Id ' + _id + ' was updated'})
        response.status_code = 200
        #Sync To Firestore
        #Whenever we crete or update an user, we call the SyncToFirestore method.
        #In fact this method can be called whenever we want in order to sync our database to Firestore.
        syncToFirestore()
        return response
    else:
      return notFound()


@app.errorhandler(404)
def notFound(error=None):
    message = {
        'message': 'Resource was not Found ' + request.url,
        'status': 404
    }
    response = jsonify(message)
    response.status_code = 404
    return response



@app.route('/', methods=['GET', 'POST'])
def loginAuthentication():
	unsuccessful = 'Bad credentials. Please check your credentials'
	successful = 'Login successful. Welcome'
	if request.method == 'POST':
		email = request.form['email']
		password = request.form['password']
		try:
			auth.sign_in_with_email_and_password(email, password)
			return render_template('login.html', s=successful)
		except:
			return render_template('login.html', us=unsuccessful)

	return render_template('login.html')




if __name__ == "__main__":
    app.run(debug=True)