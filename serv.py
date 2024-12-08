import socket,threading


s = socket.socket()
s.bind(("",8084))
s.listen()

users = []
runn = True



def accept():
    while runn:
        tmep = User(s.accept()[0])
        users.append(tmep)
        tmep.recive()
        

class User:
    toSend = ""
    def __init__(self,conn):
        self.conn = conn
        self.active = True
        self.justRcd = False
        self.justSent = False
    
    def recive(self):
        while self.active:
            try:
                what = self.conn.recv(3)
                if what.decode() == 'get':
                    self.conn.send(User.toSend)
                    print("SENT: ")
                else:
                    self.conn.send(b'ok')
                    User.toSend = self.conn.recv(5000000)
                    self.conn.send(b'thx')
                    print("GOT: ")
            except:
                users.remove(self)
                self.active = False

                # if len(users )== 0:
                #     global runn
                #     runn = False
                break


threading.Thread(target=accept).start()

