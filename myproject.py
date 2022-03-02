from flask import Flask, render_template, request, flash, redirect, session, url_for, escape, make_response
from flask_socketio import SocketIO, join_room, leave_room, emit

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
	if 'Alias' in session:
		return redirect(url_for('thezone'))
	elif request.method == 'POST':
		alias_unfiltered = request.form['alias_input']
		session['Alias'] = alias_unfiltered.upper()
		Alias = session['Alias']
		return redirect(url_for('thezone'))
	return render_template("setalias.html")

@app.route("/Anon")
def anon():
	return render_template("anon.html")

@app.route("/Contact")
def contact():
	if 'Alias' in session:
		return redirect(url_for('setalias'))
	return render_template("contact.html")

@app.route("/Info")
def info():
	return render_template("info.html")

@app.route("/Logout")
def logout():
	if 'Alias' in session:
		return render_template("logout.html")
	return redirect(url_for('setalias'))

@app.route("/TheZone", methods = ['GET','POST'])
def thezone():
	if 'Alias' in session:
		Alias = session['Alias']
		return render_template("thezone.html", alias = session['Alias'])

	return redirect(url_for('setalias'))


@app.route("/Terminate")
def terminate():
	session.pop('Alias', None)
	return redirect(url_for('setalias'))

@app.route("/SoloEngagements", methods = ['GET', 'POST'])
def soloengagements():
	if request.method == 'POST':
		room_unfiltered = request.form['room_input']
		room = room_unfiltered

		resp = make_response(redirect(url_for('sololive')))
		resp.set_cookie('room', room)
		return resp


	elif 'Alias' in session and not request.method == 'POST':
		Alias = session['Alias']
		return render_template("rooms.html", alias = session['Alias'])

	return redirect(url_for('setalias'))

@app.route("/SoloLive", methods = ['GET', 'POST'])
def sololive():
	if 'Alias' in session:
		username = session['Alias']
		room = request.cookies.get('room')
		return render_template("chat.html", username = username, room = room)
	return redirect(url_for('setalias'))

@socketio.on('send_message')
def handle_send_message_event(data):
    app.logger.info("{} has sent message to the room {}: {}".format(data['username'],
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
    socketio.run(app, debug=True)