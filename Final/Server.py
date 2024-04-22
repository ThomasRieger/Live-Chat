from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random 
from string import ascii_uppercase

# Setup Application สร้างเว็บขึ้นมา
app = Flask(__name__)
app.config["SECRET_KEY"] = "ADMIN123"
socketio = SocketIO(app)

# เก็บเลขห้องเอาไว้
rooms = {}

# generate รหัสห้อง โดยสุ่ม
def generate_room(roomnum):
    while True:
        code=""
        for _ in range(roomnum):
            code += random.choice(ascii_uppercase)
        if code not in rooms:
            break
    return code

# Redirect ไป home
@app.route("/",methods=["POST","GET"])
def home():
    # ล้าง homepage ใหม่
    session.clear()

    # การรับค่าจากผู้ใช้
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join",False) 
        create = request.form.get("create",False)
        
        # เช็ค error
        if not name:
            return render_template("home.html", error="Please enter name.",code=code,name=name)
        if join != False and not code:
            return render_template("home.html", error="Please enter room code.",code=code,name=name)
        
        # สร้างห้อง + เก็บข้อมูลที่เกิดภายในห้อง
        room = code
        # สร้างห้อง
        if create != False:
            room = generate_room(5)
            # Store Data
            rooms[room] = {"members": 0, "messages":[]}
        # เข้าห้อง
        elif code not in rooms:
            return render_template("home.html",error="Room does not exist",code=code,name=name)
        
        # เก็บค่าของผู้ใช้ชั่วคราว
        session["room"] = room
        session["name"] = name

        return redirect(url_for("room"))

    return render_template("home.html")

# Redirect ไป room
@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))
    return render_template("room.html", code=room, messages=rooms[room]["messages"])

# การเชื่อมห้อง
@socketio.on("connect")
def connect(auth):
  room = session.get("room")
  name = session.get("name")
  if not room or not name:
    return
  if room not in rooms:
    leave_room(room)
    return
  join_room(room)
  send({"name": name, "message": "has entered the room"}, to=room)
  rooms[room]["members"] += 1
  print(f"{name} joined room {room}")

# การออกห้อง
@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} lefted room {room}")

# การส่งข้อความ
@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return 
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

if __name__ == "__main__":
    socketio.run(app,host='0.0.0.0',debug=True)