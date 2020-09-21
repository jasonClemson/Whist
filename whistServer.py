#button appears for start game after one player
#figure out better height options
#status bar for bt or out of?

#import eventlet
import logging
#import pickle
#import redis
#import atexit
import json
from sys import getsizeof
from flask import Flask, render_template, redirect, request,jsonify, abort, url_for
from flask_socketio import SocketIO, join_room, leave_room, close_room, send, emit, rooms
from datetime import date,timedelta
import time
#from functools import reduce
#import sentry_sdk
#from sentry_sdk.integrations.flask import FlaskIntegration
#from dotenv import load_dotenv
import pyrebase
import random
import string
import copy

#https://pynative.com/python-generate-random-string/
def get_random_alphaNumeric_string(stringLength=8):
   lettersAndDigits = string.ascii_letters + string.digits
   return ''.join((random.choice(lettersAndDigits) for i in range(stringLength)))
   
def compVal(one, two):
    if(one.isnumeric() and two.isnumeric()):
        return int(one)>int(two)
    elif(one.isnumeric() and not two.isnumeric()):
        return False
    elif(not one.isnumeric() and two.isnumeric()):
        return True
    elif(not one.isnumeric() and not two.isnumeric()):
        if one=='X':
            return False
        if one=='a':
            return True
        if one=='j' and two=='X':
            return True
        if one=='q' and (two=='j' or two=='X'):
            return True
        if one=='k' and (two =='q' or two=='j' or two=='X'):
            return True
        return False
    
   
config = {
    ##Insert config here.  Excluded for privacy reasons.
  }
  
firebase = pyrebase.initialize_app(config)
db = firebase.database()
auth=firebase.auth()
user = auth.sign_in_with_email_and_password("teetsj19@gmail.com", "Ar!3!5n3rT!m3")

from flask import *

app= Flask(__name__)
socketio = SocketIO(app)
#app.logger.info(auth.token)
deck=["2C","3C","4C","5C","6C","7C","8C","9C","XC","jC","qC","kC","aC",
    "2H","3H","4H","5H","6H","7H","8H","9H","XH","jH","qH","kH","aH",
    "2S","3S","4S","5S","6S","7S","8S","9S","XS","jS","qS","kS","aS",
    "2D","3D","4D","5D","6D","7D","8D","9D","XD","jD","qD","kD","aD"]
   
@app.route('/', methods=['GET','POST'])
def basic():
    if request.method == 'POST':
        if request.form['submit']=='enter':
            key=request.form['gamecode']
            #game=db.child("Data").child(key).get().val()
            #game['Players']['2']=request.form['name']
            try:
                l=len(db.child("Data").child(key).child("Players").get().val())
                if db.child("Data").child(key).child("started").get().val():
                    '''try:
                        score=db.child("Data").child(key).child("left").child(request.form['name']).get().val()
                        return redirect(url_for('game',id=key))
                    except:'''
                    return redirect(url_for('gameStarted'))
                if len(db.child("Data").child(key).child("Players").get().val())-1==6:
                    return redirect(url_for('gameFull'))
                db.child("Data").child(key).child("Players").child(str(l)).set(request.form['name'])
            except:
                return redirect(url_for('badGamecode'))
            #if db.child("Data").child(key).child("Started").get().val():
            #    return redirect(url_for('badGamecode'))
            return redirect(url_for('game',id=key))#("127.0.0.1:500/game/"+key)
        elif request.form['submit']=='new game':
            #key=get_random_alphaNumeric_string()
            key=get_random_alphaNumeric_string()
            while True:
                try:
                    l=len(db.child("Data").child(key).child("Players").get().val())
                    app.logger.info("Copycat code")
                    key=get_random_alphaNumeric_string()
                except:
                    break
            #key="JASON"
            data={
            "Start_time": time.time(),
            "Players": {"1": request.form['name']},
            "turn":1,
            "trick":8,
            "Bets":{"1":-1},
            "started": False,
            "trumps":False
            }
            #identifier= db.child("Data").push().getKey()
            #info={"key":key,
            #"id":identifier
            #}
            #db.child("Keys").push(info)
            #db.child("Keys").push(key)
            db.child("Data").child(key).set(data)
            return redirect(url_for('game',id=key))#return redirect("127.0.0.1:500/game/"+key)
            #Some behavior to get to game page
    return render_template('whistWelcome.html')

@app.route('/game/<id>')
def game(id):
    return render_template('whistRoom.html',p=len(db.child("Data").child(id).child("Players").get().val())-1,k=id)
    
@app.route('/invalidGame')
def badGamecode():
    return render_template('gamecodeError.html')
    
@app.route('/rules')
def rules():
    return render_template('rules.html')
    
@app.route('/gameStartedError')
def gameStarted():
    return render_template('gameStarted.html')

@app.route('/gameFullError')
def gameFull():
    return render_template('gameFull,html')
    
@app.route('/gameOver/<id>')
def gameOver(id):
    test=[{'name':'Jason','score':100},{'name':'Julia','score':50}] 
    app.logger.info(db.child("Data").child(id).child("final_info").get().val())
    return render_template('endScreen.html',list=db.child("Data").child(id).child("final_info").get().val(),id=id,players=db.child("Data").child(id).child("Players").get().val())#db.child("Data").child(id).child("final_info").get().val(),id=id)
    
@socketio.on('create')
def on_create(data):
    """Create a game lobby"""
    join_room(data['data'])
    app.logger.info("joined room")
    emit('new_player',db.child("Data").child(data['data']).child("Players").get().val(),room=data['data'])
    
@socketio.on('card_chosen')
def on_place(data):
    app.logger.info('card_chosen')
    id=data['key']
    placer=data['placer']
    num_players=len(db.child("Data").child(id).child("Players").get().val())-1 #fix
    turn =  db.child("Data").child(id).child("turn").get().val()
    app.logger.info(data['index'])
    card= db.child("Data").child(id).child("hands").child(placer-1).child(str(int(data['index']))).get().val()
    db.child("Data").child(id).child("hands").child(placer-1).child(str(int(data['index']))).remove()##reconsider
    lead= db.child("Data").child(id).child("lead").get().val()
    app.logger.info(lead)
    app.logger.info(card)
    trump= db.child("Data").child(id).child("trump_suit").get().val()
    
    if card[1]==trump and not lead[1]==trump:
        db.child("Data").child(id).child("lead").set(card+str(placer))
    elif(card[1]==lead[1] and compVal(card[0],lead[0])):
        db.child("Data").child(id).child("lead").set(card+str(placer))
    elif(lead[1]=='X'):
        db.child("Data").child(id).child("lead").set(card+str(placer))
    
    if placer==len(db.child("Data").child(data['key']).child("Players").get().val())-1:
        if (turn==1):
            emit('card_placed', {'placer':placer,'card':card,'end':True},room=data['key'])
            '''lead= db.child("Data").child(id).child("lead").get().val()
            prev=db.child("Data").child(id).child("tricks_won").child(lead[2]).get().val()
            db.child("Data").child(id).child("tricks_won").child(lead[2]).set(prev+1)
            db.child("Data").child(id).child("turn").set(int(lead[2]))
            db.child("Data").child(id).child("lead").set('0X1')
            bet=db.child("Data").child(id).child("Bets").child(lead[2]).get().val()
            emit('round_update',{'player':lead[2],'score':prev+1,'length':num_players,'bet':bet},room=data['key'])
            emit('clear_table',room=data['key'])
            emit('choose_card',{'turn':int(lead[2]),'suit':'X'},room=data['key'])'''
        else:
            emit('card_placed', {'placer':placer,'card':card,'end':False},room=data['key'])
            emit('choose_card',{'turn':1,'suit':data['suit']}, room=data['key'])
    else:
        if (turn==placer+1):
           ''' emit('card_placed', {'placer':placer,'card':card,'end':True},room=data['key'])
            lead= db.child("Data").child(id).child("lead").get().val()
            prev=db.child("Data").child(id).child("tricks_won").child(lead[2]).get().val()
            db.child("Data").child(id).child("tricks_won").child(lead[2]).set(prev+1)
            db.child("Data").child(id).child("turn").set(int(lead[2]))
            db.child("Data").child(id).child("lead").set('0X1')
            bet=db.child("Data").child(id).child("Bets").child(lead[2]).get().val()
            emit('round_update',{'player':lead[2],'score':prev+1,'length':num_players,'bet':bet},room=data['key'])
            emit('clear_table',room=data['key'])
            emit('choose_card',{'turn':int(lead[2]),'suit':'X'},room=data['key'])'''
        else:
            emit('card_placed', {'placer':placer,'card':card,'end':False},room=data['key'])
            emit('choose_card',{'turn':placer+1,'suit':data['suit'],}, room=data['key'])
            
@socketio.on('end_round_clear')
def endClear(data):
    time.sleep(2)
    id=data['key']
    num_players=len(db.child("Data").child(id).child("Players").get().val())-1
    lead= db.child("Data").child(id).child("lead").get().val()
    prev=db.child("Data").child(id).child("tricks_won").child(lead[2]).get().val()
    db.child("Data").child(id).child("tricks_won").child(lead[2]).set(prev+1)
    db.child("Data").child(id).child("turn").set(int(lead[2]))
    db.child("Data").child(id).child("lead").set('0X1')
    emit('round_update',{'player':lead[2],'score':prev+1,'length':num_players},room=data['key'])
    emit('clear_table',room=data['key'])
    emit('choose_card',{'turn':int(lead[2]),'suit':'X'},room=data['key'])

@socketio.on('game_start')
def deal_hands(data):
    top=0
    hands=[]
    scores=[]
    max=db.child("Data").child(data['key']).child("trick").get().val()
    db.child("Data").child(data['key']).child("started").set(True)
    tempDeck=copy.deepcopy(deck)
    random.shuffle(tempDeck)
    for i in range(1,len(db.child("Data").child(data['key']).child("Players").get().val())):
        hands.append([])
        for j in range(0, max):
            app.logger.info(hands)
            hands[i-1].append(tempDeck[top])
            top=top+1
        db.child("Data").child(data['key']).child("tricks_won").child(str(i)).set(0)
        db.child("Data").child(data['key']).child('score').child(str(i)).set(0)
        scores.append(0)
    trump=tempDeck[top]
    db.child("Data").child(data['key']).child('trump_suit').set(trump[1])
    emit('trump_chosen',trump,room=data['key'])
    emit('scoreboard_update',scores,room=data['key'])
    db.child("Data").child(data['key']).child("hands").set(hands)#may or may not need
    emit('hands_dealt',hands,room=data['key'])
    emit('place_bet',{'turn':db.child("Data").child(data['key']).child("turn").get().val(),'max':max, 'exempt':9} ,room=data['key'])
    
@socketio.on('bet_placed')
def handle_bet(data):
    id=data['key']
    app.logger.info(id)
    app.logger.info(type(id))
    turn=db.child("Data").child(id).child("turn").get().val()
    max=db.child("Data").child(data['key']).child("trick").get().val()
    #numPlayers=len(db.child("Data").child(id).child("Players").get().val())-1
    numPlayers=len(db.child("Data").child(id).child("Players").get().val())-1 #fix
    placer=data['placer']
    db.child("Data").child(id).child("Bets").child(str(placer)).set(int(data['bet']))
    app.logger.info(placer)
    if (placer+1)==turn or (placer==numPlayers and turn==1):
        db.child("Data").child(id).child("lead").set("0X1")
        emit('choose_card', {'turn':turn,'suit':'X'},room=data['key'])
        bets=db.child("Data").child(id).child("Bets").get().val()
        emit('bet_status_set',bets,room=id)
    else: 
        if placer==numPlayers:
            placer=0
        placer=placer+1
        if placer==numPlayers and turn==1 or placer+1==turn:
            bets= len(db.child("Data").child(id).child("Bets").get().val())#FIX
            #b=bets.val()
            #app.logger.info(b.values())
            #app.logger.info(b[0])
            sum=0
            #for bet in bets.each():
            #    app.logger.info(bet.get().val())
            #    app.logger.info(b[bet])
            #    sum=sum+(b[bet])'''
            for i in range(1,bets):
                sum=sum+db.child("Data").child(id).child("Bets").child(str(i)).get().val()
            emit('place_bet',{'turn':placer,'max':max,'exempt':max-sum} ,room=data['key'])
        else:
            emit('place_bet',{'turn':placer,'max':max,'exempt':9} ,room=data['key'])#fix later
            
@socketio.on('next_round')
def new_round(data):
    id=data['key']
    numPlayers=len(db.child("Data").child(data['key']).child("Players").get().val())-1
    trick=db.child("Data").child(data['key']).child("trick").get().val()
    trumps=db.child("Data").child(data['key']).child("trumps").get().val()
    if trumps:
        if trick>1:
            trick=trick-1
        else:
            db.child("Data").child(data['key']).child("trumps").set(not trumps)
            trumps= not trumps
    else:
        if trick==8:
            final_data=[]
            app.logger.info('Reached end')
            scores=[]
            for i in range(1,numPlayers+1):
                name=db.child("Data").child(id).child('Players').child(str(i)).get().val()
                tricks_won=db.child("Data").child(data['key']).child('tricks_won').child(str(i)).get().val()
                score=db.child("Data").child(data['key']).child('score').child(str(i)).get().val()
                if tricks_won==db.child("Data").child(data['key']).child('Bets').child(str(i)).get().val():
                    score=score+10
                score=score+tricks_won
                scores.append(score)
                db.child("Data").child(data['key']).child("tricks_won").child(str(i)).set(0)
                db.child("Data").child(data['key']).child('score').child(str(i)).set(score)
                summary={
                    'score':score,
                    'name':name
                };
                final_data.append(summary)
            final_data=sorted(final_data, key = lambda i: i['score'], reverse=True)
            app.logger.info(final_data)
            db.child("Data").child(id).child('final_info').set(final_data)
            emit('game_over', room=id)
            return redirect(url_for('gameOver',id=id))
        else:
            trick=trick+1
    db.child("Data").child(data['key']).child("trick").set(trick)
    
    top=0
    hands=[]
    scores=[]
    max=trick
    tempDeck=copy.deepcopy(deck)
    random.shuffle(tempDeck)
    for i in range(1,numPlayers+1):
        hands.append([])
        for j in range(0, max):
            app.logger.info(hands)
            hands[i-1].append(tempDeck[top])
            top=top+1
        tricks_won=db.child("Data").child(data['key']).child('tricks_won').child(str(i)).get().val()
        score=db.child("Data").child(data['key']).child('score').child(str(i)).get().val()
        if tricks_won==db.child("Data").child(data['key']).child('Bets').child(str(i)).get().val():
            score=score+10
        score=score+tricks_won
        scores.append(score)
        db.child("Data").child(data['key']).child("tricks_won").child(str(i)).set(0)
        db.child("Data").child(data['key']).child('score').child(str(i)).set(score)
    if trumps:
        trump=tempDeck[top]
        db.child("Data").child(data['key']).child('trump_suit').set(trump[1])
        emit('trump_chosen',trump,room=data['key'])
    else:
        emit('trumpless_set',room=data['key'])
    emit('scoreboard_update',scores,room=data['key'])
    db.child("Data").child(data['key']).child("hands").set(hands)#may or may not need
    emit('hands_dealt',hands,room=data['key'])
    emit('place_bet',{'turn':db.child("Data").child(data['key']).child("turn").get().val(),'max':max, 'exempt':9} ,room=data['key'])
    
@socketio.on('end_connect')
def end_connect(data):
    #join_room(data)
    db.child("Data").remove(data)
    
@socketio.on('player_left')
def on_leave(data):
    player=data['player']
    left_info=[]
    name=db.child("Data").child(data['data']).child("Players").child(player).get().val()
    try:
        score=db.child("Data").child(data['data']).child("score").child(player).get().val()
        db.child("Data").child(data['data']).child("left").child(name).set(score)
    except:
        app.logger.info('game not started')
    for i in range(player,len(db.child("Data").child(data['data']).child("Players").get().val())-1):
        swap=db.child("Data").child(data['data']).child("Players").child(str(i+1)).get().val()
        db.child("Data").child(data['data']).child("Players").child(str(i)).set(swap)
        if db.child("Data").child(data['data']).child("started").get().val():
            swap=db.child("Data").child(data['data']).child("score").child(str(i+1)).get().val()
            db.child("Data").child(data['data']).child("score").child(str(i)).set(swap)
    numPlayers=len(db.child("Data").child(data['data']).child("Players").get().val())-1
    if numPlayers==1:
        db.child("Data").child(data['data']).remove()
    else:
        db.child("Data").child(data['data']).child("Players").child(str(numPlayers)).remove()
        emit('someone_left', {'player':data['player']},room=data['data'])
        emit('new_player',db.child("Data").child(data['data']).child("Players").get().val(),room=data['data'])#replace with some other mechanism
    
    trumps=db.child("Data").child(data['data']).child("trumps").get().val()
    trick=db.child("Data").child(data['data']).child("trick").get().val()
    top=0
    hands=[]
    scores=[]
    max=trick
    tempDeck=copy.deepcopy(deck)
    random.shuffle(tempDeck)
    for i in range(1,numPlayers):
        hands.append([])
        for j in range(0, max):
            app.logger.info(hands)
            hands[i-1].append(tempDeck[top])
            top=top+1
        db.child("Data").child(data['data']).child("tricks_won").child(str(i)).set(0)
        score=db.child("Data").child(data['data']).child('score').child(str(i)).get().val()
        scores.append(score)
    if trumps:
        trump=tempDeck[top]
        db.child("Data").child(data['data']).child('trump_suit').set(trump[1])
        emit('trump_chosen',trump,room=data['data'])
    else:
        emit('trumpless_set',room=data['data'])
    db.child("Data").child(data['data']).child("hands").set(hands)#may or may not need
    emit('scoreboard_update',scores,room=data['data'])
    emit('hands_dealt',hands,room=data['data'])
    emit('place_bet',{'turn':db.child("Data").child(data['data']).child("turn").get().val(),'max':max, 'exempt':9} ,room=data['data'])
    
'''@socketio.on('replay')
def replay_connect(data):
    app.logger.info(data['id'])
    key=get_random_alphaNumeric_string()
    while True:
        try:
            l=len(db.child("Data").child(key).child("Players").get().val())
            app.logger.info("Copycat code")
            key=get_random_alphaNumeric_string()
        except:
            break
    #key="JASON"
    info={
    "Start_time": time.time(),
    "Players": data['players'],
    "turn":1,
    "trick":8,
    "Bets":{"1":-1},
    "started": False,
    "trumps":False
    }
    db.child("Data").child(key).set(info)
    emit('redirect',{'extend':key},room=data['id'])'''
    

if __name__ =='__main__':
    socketio.run(app,debug=True)
