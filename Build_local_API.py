from flask import Flask
from flask_restful import Resource, Api, reqparse
from flask_bcrypt import Bcrypt, generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager
from flask_jwt_extended import create_access_token
from flask_jwt_extended import jwt_required
import pandas as pd
import requests
import hashlib
import time
import datetime
from forex_python.converter import CurrencyRates

app = Flask(__name__)
api = Api(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
app.config["JWT_SECRET_KEY"] = "qwertyuiop1029384756"

#Create a function to replace zeros
def replace_zeros(df, column_name):
    df[column_name].replace(to_replace = 0, value = None, inplace = True)

#This function has been created to avoid repetitive code every time we want to create a new entry
def createEntry(df, name, ID, events, series, comics, price):
    entry = pd.DataFrame({'Character Name': name,
                         'Character ID': ID,
                         'Total Available Events': events,
                         'Total Available Series': series,
                         'Total Available Comics': comics,
                         'Price of the Most Expensive Comic': price}, index = [0])
    return entry

def hash_password(password):
        return generate_password_hash(password).decode('utf8')


class Characters(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('characterName', type=str, action='append', help='Missing argument characterName', required = False, location='args')
        parser.add_argument('characterID', type=int, action='append', help='Missing argument characterID', required = False, location='args')
        args = parser.parse_args()
        df = pd.read_csv("data.csv")
        
        if args['characterName'] is not None: #if one or more characterName are provided
            if all(item in list(df['Character Name']) for item in args['characterName']):
                df = df.loc[df['Character Name'].isin(args['characterName'])]
                return {'status': 200,
                        'response': df.to_dict(orient='records')}, 200
            else:
                return {'status': 404,
                        'response': "Incorrect values for characterName."}, 404
        
        elif args['characterID'] is not None: #if one or more characterID are provided
            if all(item in list(df['Character ID']) for item in args['characterID']):
                df = df.loc[df['Character ID'].isin(args['characterID'])]
                return {'status': 200,
                        'response': df.to_dict(orient='records')}, 200
            else:
                return {'status': 404,
                        'response': "Incorrect values for characterID."}, 404
            
        else: #if both fields are not provided, we return all the df
            return {'status': 200,
                    'response': df.to_dict(orient='records')}, 200
                 
    
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('Authorization', type=str, help="token is required", required=True, location='headers')
        parser.add_argument('characterName', type=str, help='Missing argument characterName', required = False, location='args')
        parser.add_argument('characterID', type=int, help='Missing argument characterID', required = True, location='args')
        parser.add_argument('events', type=int, help='Missing argument events', required = False, location='args')
        parser.add_argument('series', type=int, help='Missing argument series', required = False, location='args')
        parser.add_argument('comics', type=int, help='Missing argument comics', required = False, location='args')
        parser.add_argument('price', type=float, help='Missing argument price', required = False, location='args')
        args = parser.parse_args()
        df = pd.read_csv("data.csv")
        
        #if the id provided is in the list, message that it already exists
        if args['characterID'] in list(df['Character ID']):
            return {'status': 409,
                    'response': f"{args['characterID']} already exists."}, 409
        
        #if it is not in the list yet, there are different possibilities
        else:
            #if all the arguments are provided, the character is added directly
            if all(v is not None for v in [args['characterName'], args['events'], args['series'], args['comics'], args['price']]):
                entry = createEntry(df, args['characterName'], args['characterID'],
                                    args['events'], args['series'], args['comics'], args['price']) #create the new entry
                replace_zeros(entry, 'Total Available Events'), replace_zeros(entry, 'Total Available Series'), 
                replace_zeros(entry, 'Total Available Comics'), replace_zeros(entry, 'Price of the Most Expensive Comic') #replace the zeros with None
                df = df.append(entry, ignore_index = True) #append the entry to the df
                df.to_csv('data.csv', index = False) #save the df to csv
                entry = df.loc[df['Character ID'] == args['characterID']] # take the new entry from the df
                return {'status': 200,
                        'response': entry.to_dict(orient='records')}, 200 #return the entry in dictionary form and 200 OK
            
            #if only the characterID is provided, the API sends a get request to the correct Marvel URI to retrieve the information on the
            # remaining parameters
            elif all(v is None for v in [args['characterName'], args['events'], args['series'], args['comics'], args['price']]):
                urlCharacter = "http://gateway.marvel.com/v1/public/characters" + "/" + str(args['characterID']) #concat strings to form URI
                public_key = "46180a82e99e236b44c9ebb179e70221"
                private_key = "6c45f0f25e79ad46609977d2a2d3c883426dc29b"
                timestamp_str = str(time.time())
                hash_1 = timestamp_str+private_key+public_key
                hash_2 = hashlib.md5(hash_1.encode())
                hashkey = hash_2.hexdigest()
                response = requests.get(urlCharacter, params = {"apikey": public_key, "ts": timestamp_str, "hash": hashkey})
                
                # if the character does not exist, a 404 is returned
                if response.status_code == 404:
                    return {'status': 404, 
                            'response': "Character not found"}, 404
                
                # if the character is found, we store the data in variables and we create the entry as before, calling the func. createEntry
                else:
                    response = response.json()
                    name = response['data']['results'][0]['name']
                    events = response['data']['results'][0]['events']['available']
                    series = response['data']['results'][0]['series']['available']
                    comics = response['data']['results'][0]['comics']['available']
                    
                    
                    #To get the max price we use the same code of part 1 but without looping on the characters (we only have 1)
                    resp_comics = requests.get(response['data']['results'][0]['comics']['collectionURI'],
                                               params={"apikey": public_key,
                                                       "ts": timestamp_str,
                                                       "hash": hashkey,
                                                       'characterId': response['data']['results'][0]['id']})
                    resp_comics = resp_comics.json()
                    max_price = 0
                    for comic in resp_comics['data']['results']:
                        if comic['prices'][0]['price'] > max_price:
                            max_price = comic['prices'][0]['price']
                    if max_price == 0:
                        price = None
                    else:
                        price = float(max_price)
                        
                    entry = createEntry(df, name, args['characterID'], events, series, comics, price) #create the new entry
                    replace_zeros(entry, 'Total Available Events'), replace_zeros(entry, 'Total Available Series'), replace_zeros(entry, 'Total Available Comics') #replace 0s
                    df = df.append(entry, ignore_index = True) #append the entry to the df
                    df.to_csv('data.csv', index = False) #save the df to csv
                    entry = df.loc[df['Character ID'] == args['characterID']] # take the new entry from the df
                    return {'status': 200,
                            'response': entry.to_dict(orient='records')}, 200 #return the entry in dictionary form and 200 OK
            
            #if the characterID is provided with some other parameters (but not all), a message "missing values" is returned
            else:
                return {'status': 404, 
                        'response': "Missing values"}, 404
            
            
    
    @jwt_required()
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('Authorization', type=str, help="token is required", required=True, location='headers')
        parser.add_argument('characterName', type=str, action='append', help='Missing argument characterName',
                            required = False, location='args')
        parser.add_argument('characterID', type=int, action='append', help='Missing argument characterID',
                            required = False, location='args')
        args = parser.parse_args()
        df = pd.read_csv("data.csv")
        
        if args['characterName'] is not None: #if one or more characterName are provided
            if all(item in list(df['Character Name']) for item in args['characterName']): #check if all the names provided are in the df
                df = df.loc[df['Character Name'].isin(args['characterName']) == False] #take only the rows whose characterNames are different
                df.to_csv('data.csv', index = False) #save the df to csv
                return {'status': 200,
                        'response': df.to_dict(orient='records')}, 200
            else: #if not all the names are in the df, show message "incorrect values"
                return {'status': 404,
                        'response': "Incorrect values for characterName."}, 404
        
        elif args['characterID'] is not None: #if one or more characterID are provided
            if all(item in list(df['Character ID']) for item in args['characterID']): #check if all the ID provided are in the df
                df = df.loc[df['Character ID'].isin(args['characterID']) == False] #take only the rows whose characterIDs are different
                df.to_csv('data.csv', index = False) #save the df to csv
                return {'status': 200,
                        'response': df.to_dict(orient='records')}, 200
            else: #if not all the IDs are in the df, show message "incorrect values"
                return {'status': 404,
                        'response': "Incorrect values for characterID."}, 404
            
        else: #if both fields are not provided, show message stating that some field must be provided
            return {'status': 404,
                    'response': 'Provide characterName (1 or more) or characterID (1 or more)'}, 404

    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument('characterName', type=str, help='Missing argument Character Name', required=False, location='args')
        parser.add_argument('characterID', type=int, help='Missing argument Character ID', required=False, location='args')
        parser.add_argument('price', type=float, help='Missing argument price', required=True, location='args')
        parser.add_argument('currency', type=str, help='Missing argument currency', required=False, location='args') # specifies which currency the new price is provided in (allows for any currency, incl. USD, EUR, GBP & CAD)
        args = parser.parse_args()

        data = pd.read_csv('data.csv')
        
        if args['characterName'] is None and args['characterID'] is None: # a name or ID is needed to modify the right price
            return {'status': 404, 'response': f'Missing Character Name or Character ID'}, 404 
        if args['characterName'] is not None and args['characterID'] is not None: # either name or ID of character must be provided (both are not possible)
            return {'status': 400, 'response': f'Provide either character name or ID'}, 400
        
        if args['characterName'] is not None: # if a character name is provided: 
            if args['characterName'] not in list(data['Character Name']): # character name has to be in the data file
                return {'status': 409, 'response': f"Incorrect value {args['characterName']} for Character Name."}, 409
            else: 
                if args['currency'] is None: # if no currency is provided, it is assumed that the price is in USD
                    data.loc[data['Character Name']==args['characterName'], 'Price of the Most Expensive Comic'] = args['price']
                    data.to_csv('data.csv', index=False)
                    entry = data.loc[data['Character Name']==args['characterName']].to_dict(orient='records')
                    return {'status': 200, 'response': entry}, 200 
                else: # if a currency is provided: convert the price in the given currency to USD
                    data.loc[data['Character Name']==args['characterName'], 'Price of the Most Expensive Comic'] = round(args['price']* (CurrencyRates().get_rate(args['currency'], 'USD')),2) # the provided price is multiplied with the current exchange rate to USD 
                    data.to_csv('data.csv', index=False)
                    entry = data.loc[data['Character Name']==args['characterName']].to_dict(orient='records')
                    return {'status': 200, 'response': entry}, 200
                
        elif args['characterID'] is not None: # if a character ID is provided:
            if args['characterID'] not in list(data['Character ID']): # character ID has to be in the data file
                return {'status': 409, 'response': f"Incorrect value {args['characterID']} for Character ID."}, 409
            else: 
                if args['currency'] is None: # if no currency is provided, it is assumed that the price is in USD
                    data.loc[data['Character ID']==args['characterID'], 'Price of the Most Expensive Comic'] = args['price']
                    data.to_csv('data.csv', index=False)
                    entry = data.loc[data['Character ID']==args['characterID']].to_dict(orient='records')
                    return {'status': 200, 'response': entry}, 200 
                else: # if a currency is provided, the price is converted from the given currency to USD
                    data.loc[data['Character ID']==args['characterID'], 'Price of the Most Expensive Comic'] = round(args['price']* (CurrencyRates().get_rate(args['currency'], 'USD')),2) # the provided price is multiplied with the current exchange rate to USD 
                    data.to_csv('data.csv', index=False)
                    entry = data.loc[data['Character ID']==args['characterID']].to_dict(orient='records')
                    return {'status': 200, 'response': entry}, 200      
        
        
class SignUp(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, help='Missing argument email', required=True, location='args')
        parser.add_argument('password', type=str, help='Missing argument password', required=True, location='args')
        args = parser.parse_args()
        
        #try except block, so if the file does not exist yet (so error opening it) it is created for the first time
        
        df = pd.DataFrame(columns=['email', 'password'])
        df.to_csv('users.csv', index=False)
        
      
        df = pd.read_csv('users.csv')
        
        #if the email provided is already existing, no need to signup again, so message "mail already exists"
        #if args['email'] in list(df['email']):
            #return {'status': 409, 'response': f"{args['email']} already exists."}, 409
        #else: #otherwise, a new entry with email and hashed psw is created
        entry = pd.DataFrame({
            'email': [args['email']],
            'password': [hash_password(args['password'])]
        })

        df = df.append(entry, ignore_index=True) #the entry is appended to the df
        df.to_csv('users.csv', index=False)  # save back to CSV

        return {'status': 200, 'response': "Successfully added"}, 200 # return the df and 200 OK
        
        
class LogIn(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, help='Missing argument email', required=True, location='args')
        parser.add_argument('password', type=str, help='Missing argument password', required=True, location='args')
        args = parser.parse_args()
        df = pd.read_csv('users.csv') #read csv file to df
        
        #if email is not in the list, login is not possible so message "invalid email"
        if args['email'] not in list(df['email']):
            return {'status': 401, 'response': f"Invalid email"}, 401
        
        else: #if email is correct
            password = df.loc[df['email']==args['email'], 'password'][0] #filter the row for that email and take the hashed password
            
            #use the check_password_hash to verify if the password provided is the same of the one that was previously hashed
            if check_password_hash(password, args['password']):
                expires = datetime.timedelta(hours=1) #set the expiring time to 1 hour
                token = create_access_token(identity=str(df.loc[df['email']==args['email']].index[0]), expires_delta=expires) #create token
                return {'status': 200, 'response': 'Successfully logged in', 'token': token}, 200 # return the df and 200 OK
            else: #if the password is not the same, return 401
                return {'status': 401, 'response': f"Invalid password"}, 401
            

    
                
api.add_resource(Characters, '/characters', endpoint = 'characters')
api.add_resource(SignUp, '/signup', endpoint='signup')
api.add_resource(LogIn, '/login', endpoint='login')

if __name__ == '__main__':
    app.run(debug=True)