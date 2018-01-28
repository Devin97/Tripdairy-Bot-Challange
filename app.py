from flask import Flask, render_template, request
import apiai
from flask_sqlalchemy import SQLAlchemy
import json
import yaml

CLIENT_ACCESS_TOKEN = "e7e7949784b2442db9fd5fb23c61cc06"

SESSION_ID = "0f0bbe63-9fc2-4de2-a8aa-81f6aec2596c"

app = Flask(__name__)

##################  DATABASE #####################################
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'

db = SQLAlchemy(app)

db.Model.metadata.reflect(db.engine)

class Hotel(db.Model):

    __table__ = db.Model.metadata.tables['hotel1']
    
    def __repr__(self):
        return self.address

##################################################################

ai = apiai.ApiAI(CLIENT_ACCESS_TOKEN)


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg')
    req = ai.text_request()
    req.lang = 'en'
    req.session_id = SESSION_ID
    req.query = userText
    response = req.getresponse()
    response = response.read()
    resp = response.decode('UTF-8')
    try:
        #print(json.loads(resp)["alternateResult"]["resolvedQuery"])
        try:
            hotel_name = json.loads(resp)["result"]["parameters"]["hotel_name"]
            if hotel_name:
                address = get_hotel_address(resp, hotel_name)
                return str(address)

            if json.loads(resp)["result"]["fulfillment"]["speech"]:
                return json.loads(resp)["result"]["fulfillment"]["speech"]
            else:
                result = unhandled_queries(resp)
                return result
            
        except Exception as e:
            pass #print(str(e))

        try:
            wifi_password = json.loads(resp)["result"]["parameters"]["wifi_password"]
            if wifi_password:
                hotel_name = json.loads(resp)["result"]["contexts"][0]["parameters"]["hotel_name"]
                password = get_wifi_password(resp, hotel_name)
                return str(password)

            if json.loads(resp)["result"]["fulfillment"]["speech"]:
                return json.loads(resp)["result"]["fulfillment"]["speech"]
            else:
                result = unhandled_queries(resp)
                return result
            
        except Exception as e:
            pass #print(str(e))

        try:
            room = json.loads(resp)["result"]["parameters"]["rooms"]
            if room:
                hotel_name = json.loads(resp)["result"]["contexts"][0]["parameters"]["hotel_name"]
                answer = check_room(resp, hotel_name)
                return str(answer)

            if json.loads(resp)["result"]["fulfillment"]["speech"]:
                return json.loads(resp)["result"]["fulfillment"]["speech"]
            else:
                result = unhandled_queries(resp)
                return result
            
        except Exception as e:
            pass #print(str(e))

        if json.loads(resp)["result"]["fulfillment"]["speech"]:
            return json.loads(resp)["result"]["fulfillment"]["speech"]
        else:
            result = unhandled_queries(resp)
            return result
        
    except Exception as e:
        return json.loads(resp)["result"]["fulfillment"]["speech"]

def unhandled_queries(resp):
    try:
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.append([json.loads(resp)["alternateResult"]["resolvedQuery"]])
        wb.save("unhandled.csv")
        #file = open("unhandled.csv", "w")
        #file.write(json.loads(resp)["alternateResult"]["resolvedQuery"]+"\n")
        #file.close()
        return "I did not understand that."
    except Exception as e:
        print(str(e))

def get_hotel_address(resp, hotel_name):
    resp = json.loads(resp)["result"]["fulfillment"]["speech"]
    address = Hotel.query.filter_by(name=hotel_name).first()
    #if hotel_name:
    return str(address)

def get_wifi_password(resp, hotel_name):

    with open("password.yml", 'r') as stream:
        try:
            hotel_name = hotel_name.replace(" ", "-")
            password = yaml.load(stream)[hotel_name]
            return "Password of "+hotel_name.replace("-", " ").title()+" is \'"+password+"\' (without quotes)."
        except yaml.YAMLError as exc:
            print(exc)
            

def check_room(resp, hotel_name):

    try:

        date = json.loads(resp)["result"]["contexts"][0]["parameters"]["date"]
        hotel = Hotel.query.filter_by(name=hotel_name, on_date=date).first()
        if hotel.available_room != 0:
            return "Yes! rooms are available on "+date
        else:
            return "No..rooms are not available on "+date
    except Exception as e:
        pass #print(str(e))
    

if __name__ == "__main__":
    app.run()
