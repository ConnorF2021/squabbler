from flask import Flask, render_template, request, flash, redirect, session, url_for, escape, make_response
from flask_socketio import SocketIO, join_room, leave_room, emit
import random
import string

app = Flask(__name__)
socketio = SocketIO(app)

import secrets
secret_key = secrets.token_hex(16)
app.config['SECRET_KEY'] = secret_key

@app.route("/", methods = ['GET','POST'])
def landing():
	if 'Alias' in session:
		return redirect(url_for('thezone'))
	return redirect(url_for('setalias'))

@app.route("/SetAlias", methods = ['GET','POST'])
def setalias():
	if 'UserID' in session and (len(session['UserID']) == 30):
		return redirect(url_for('thezone'))
	elif request.method == 'POST':
		alias_unfiltered = request.form['alias_input']
		if (len(alias_unfiltered) < 3) or (len(alias_unfiltered) > 12):
			return redirect(url_for('setalias'))
		else:
			Alias = alias_unfiltered.upper()
			letters = string.punctuation
			session["UserID"] = ( ''.join(random.choice(letters) for i in range(30)) )
			resp = make_response(redirect(url_for('thezone')))
			resp.set_cookie('Alias', Alias)
			return resp
	return render_template("setalias.html")

@app.route("/Anon")
def anon():
	return render_template("anon.html")

@app.route("/Contact")
def contact():
	if 'UserID' in session:
		return render_template("contact.html")
	return redirect(url_for('setalias'))
	

@app.route("/Info")
def info():
	return render_template("info.html")

@app.route("/Logout")
def logout():
	if 'UserID' in session:
		return render_template("logout.html")
	return redirect(url_for('setalias'))

@app.route("/TheZone", methods = ['GET','POST'])
def thezone():
	if 'UserID' in session and (len(session['UserID']) == 30):
		Alias = request.cookies.get('Alias')
		return render_template("thezone.html", alias = Alias)

	return redirect(url_for('setalias'))


@app.route("/Terminate")
def terminate():
	session.pop('UserID', None)
	resp = make_response(redirect(url_for('setalias')))
	resp.set_cookie('Alias', 'None', max_age=0)
	resp.set_cookie('roomID', 'None', max_age=0)
	return resp

@app.route("/SoloSquabble", methods = ['GET', 'POST'])
def solosquabble():
	if 'UserID' in session and request.method == 'POST' and (len(session['UserID']) == 30):
		room_unfiltered = request.form['room_input']
		roomID = room_unfiltered

		resp = make_response(redirect(url_for('sololive')))
		resp.set_cookie('roomID', roomID)
		return resp


	elif 'UserID' in session and not request.method == 'POST' and (len(session['UserID']) == 30):
		Alias = request.cookies.get('Alias')
		return render_template("rooms.html", alias = Alias)

	return redirect(url_for('setalias'))

@app.route("/CreateSquabble", methods = ['GET', 'POST'])
def createsquabble():
	if 'UserID' in session and request.method == 'POST' and (len(session['UserID']) == 30):
		topic_unfiltered = request.form['topic_input']
		topic = topic_unfiltered
		
		desc_unfiltered = request.form['desc_input']
		desc = desc_unfiltered

		digits = string.digits
		roomID = ( ''.join(random.choice(digits) for i in range(50)) )

		resp = make_response(redirect(url_for('sololive')))
		resp.set_cookie('roomID', roomID)
		return resp


	elif 'UserID' in session and not request.method == 'POST' and (len(session['UserID']) == 30):
		Alias = request.cookies.get('Alias')
		return render_template("createroom.html", alias = Alias)

	return redirect(url_for('setalias'))

@app.route("/SoloLive", methods = ['GET', 'POST'])
def sololive():
	if 'UserID' in session:
		username = request.cookies.get('Alias')
		roomID = request.cookies.get('roomID')
		UserID = session['UserID']
		return render_template("chat.html", username = username, room = roomID, UserID=UserID)
	return redirect(url_for('setalias'))

@socketio.on('send_message')
def handle_send_message_event(data):
    app.logger.info("{} has sent message to the room {}: {}".format(data['UserID'],
                                                                    data['room'],
                                                                    data['message']))
    socketio.emit('receive_message', data, room=data['room'])


@socketio.on('join_room')
def handle_join_room_event(data):
    app.logger.info("{} has joined the room {}".format(data['username'], data['room']))
    join_room(data['room'])
    socketio.emit('join_room_announcement', data, room=data['room'])


@socketio.on('leave_room')
def handle_leave_room_event(data):
    app.logger.info("{} has left the room {}".format(data['username'], data['room']))
    leave_room(data['room'])
    socketio.emit('leave_room_announcement', data, room=data['room'])


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)