import pyrebase

#Use this program to create users on firebase.
#Once they are created, we will test them on the login web page using whe web API
####################################
#Firebase auth
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

email = input ('Please enter your email')
password = input ('Please enter your password')

"""
#Create account
user = auth.create_user_with_email_and_password(email, password)
print(auth.get_account_info(user['idToken']))
"""

###Login

user = auth.sign_in_with_email_and_password(email, password)
auth.send_email_verification(user['idToken'])
print(auth.get_account_info(user['idToken']))




####################################