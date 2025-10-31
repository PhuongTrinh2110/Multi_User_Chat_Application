import socket
import threading
from tabulate import tabulate #cài "pip3 install tabulate" qua terminal trước khi chạy
import os

#Tạo danh sách cho các clients
List_clients = {}
'''Dùng dictionary lưu trữ
key = nickname, value = conn'''

#Broadcast tin nhắn cho clients ngoại trừ sender
def Broadcast(sender_conn, mess):
    for client in List_clients.values():
        if client != sender_conn:               
            client.sendall(mess.encode('utf-8'))

#Gửi danh sách người dùng online cho conn có yêu cầu
def User_list(conn): 
    user_list = "\033[1mNgười đang online:\033[0m\n"
    for nickname in List_clients.keys():
        user_list += f"- {nickname}\n"
    conn.sendall(user_list.encode('utf-8'))

#Gửi danh mục các chức năng hỗ trợ
def get_help():
    #Tạo một list gồm các list con
    List_function = [
        ["1","/list", "Xem danh sách người đang online"],
        ["2","/rename", "Đổi nickname"],
        ["3","/bye", "Thoát trò chuyện"],
        ["4","/clear", "Xóa cuộc hội thoại"],
        ["5","@<nickname>_<message>", "Gửi tin nhắn riêng tư"],
        ["6","/help", "Xem danh sách chức năng"]
        ]
    Title = "\033[1mDanh sách các chức năng hỗ trợ\033[0m\n"
    Table = tabulate(List_function, headers=["STT","Lệnh", "Mô tả"], tablefmt="simple_outline")
    return Title + Table + "\n"
        
#Gửi tin nhắn riêng tư từ 1 client đến 1 client khác
def Private_message(sender_nickname, recv_nickname, mess):
    #Kiểm tra xem nick name có trong danh sách không?
    if recv_nickname in List_clients.keys():
        recv_conn = List_clients[recv_nickname]
        message = "\033[1mPrivate message\033[0m from\n" + sender_nickname + ": " + mess
        recv_conn.sendall(message.encode('utf-8'))
    #Nếu không có trong danh sách hoặc đã off
    else:
        sender_conn = List_clients[sender_nickname]
        sender_conn.sendall(f"\033[31m{recv_nickname} không tồn tại hoặc đã off\033[0m".encode('utf-8'))

#Yêu cầu tạo nickname cho clients, trả về giá trị nickname
def Nickname_input(conn):
    while True:
        conn.sendall("\033[1mVui lòng nhập nick name, không có khoảng trắng\033[0m".encode('utf-8'))
        nickname = conn.recv(1024).decode('utf-8')
        #Kiểm tra nick name không rỗng, không khoảng trắng và không trùng
        if not nickname:
            conn.sendall("\033[31mNickname sai cú pháp\033[0m".encode('utf-8'))
            continue
        if " " in nickname:
            conn.sendall("\033[31mNickname không được chứa khoảng trắng\033[0m".encode('utf-8'))
            continue
        if nickname in List_clients.keys():
            conn.sendall("\033[31mNickname đã có, hãy nhập nickname khác\033[0m".encode('utf-8'))
            continue
        break
    #Khi nickname đã hợp lệ
    conn.sendall("OKay".encode('utf-8'))
    List_clients[nickname] = conn
    mess = f"\033[1m{nickname} đã tham gia trò chuyện\033[0m"
    Broadcast(conn, mess)
    return nickname

#Đổi tên, trả về giá trị new_nickname
def Rename(old_nickname, conn):
    conn.sendall(f"\033[1mBạn đã yêu cầu đổi nickname\033[0m".encode('utf-8'))
    new_nickname = Nickname_input(conn)
    Broadcast(conn, f"\033[37m  ({old_nickname} đổi tên thành {new_nickname})\033[0m")
    del List_clients[old_nickname]
    conn.sendall(f"\033[1mNickname đã đổi thành: {new_nickname}\033[0m".encode('utf-8'))
    return new_nickname

#Xử lý client, tạo luồng riêng để các client có thể chạy song song các tác vụ trong bước này
def Handle_client(conn):
    #Bước đầu, người dùng đặt nickname
    nickname = Nickname_input(conn)
    while True:
        try:
            mess = conn.recv(1024).decode('utf-8').strip()
            if not mess:
                break
            #Trường hợp người dùng muốn gửi tin nhắn riêng tư bằng @<nickname>_<mess>
            elif mess.startswith("@"):
                mess = mess[1:] #Bỏ dấu "@"
                parts = mess.split(" ", 1) #Tách làm 2 phần <nickname> & <message>
                if len(parts) < 2:
                    conn.sendall("\033[31mSai cú pháp, dùng @<nickname>_<message> để gửi tin nhắn riêng tư\033[0m".encode('utf-8'))
                else:
                    Private_message(nickname, parts[0], parts[1])
            #Trường hợp client yêu cầu danh sách online
            elif mess == "/list":
                User_list(conn)
            #Trường hợp client yêu cầu đổi tên
            elif mess == "/rename":
                nickname = Rename(nickname, conn)
            #Trường hợp client yêu cầu danh sách chức năng hỗ trợ
            elif mess == "/help":
                conn.sendall(get_help().encode('utf-8'))
            #Trường hợp client gửi tin nhắn cho tất cả mọi người
            else:
                Broadcast(conn, f"{nickname}: {mess}")
                #Trường hợp người dùng say "bye"
                if mess.lower() == "/bye":
                    Broadcast(conn, f"\033[31m{nickname} đã rời khỏi cuộc trò chuyện\033[0m")
                    del List_clients[nickname]
                    conn.close()
                    break
        #Nếu người dùng ngắt kết nối đột ngột    
        except:
            #Hiển thị thông báo bên server
            print("Error in connection with", conn, "nickname", nickname)
            #Thông báo cho các client còn lại
            Broadcast(conn, f"\033[31m{nickname} đã rời khỏi cuộc trò chuyện\033[0m")
            conn.close() #Đóng kết nối với client bị ngắt đó và xóa khỏi list
            del List_clients[nickname]
            break

#Phần chính
def main():
    
    host = '192.168.100.107'    #Nhập IP máy server
    port = 63214                #>50000

    #Tạo socket, gán IP và port server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    print("Server is ready for connect at ", (host, port))
   
    try:
        while True:
            conn, addr = server.accept() #Server chấp nhận kết nối
            print("Client from", addr)
            
            #Khi đã có conn, thì tạo luồng riêng để xử lý conn đó
            if conn:
                t = threading.Thread(target=Handle_client, args=(conn,), daemon=True)
                t.start()
            else:
                try:
                    conn.close()
                except:
                    pass
    except KeyboardInterrupt:
        print("\n[INFO] Server shutting down...")
if __name__ == "__main__":
    main()

