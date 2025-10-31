import socket
import threading
import sys
import os

#Nhập IP Server, port > 50000
host = '192.168.100.107' 
port = 63214

'''Ở phần này, em tạo 2 luồng nhận và gửi tin nhắn riêng
Nhằm dễ dàng nhắn và nhận nhiều tin nhắn liên tục mà không cần phải đợi'''

#Đặt biến start=true => đồng bộ sự ngắt kết nối của send và recv
start = True

#Hàm nhận tin nhắn
def receive(client):
    while start:
        try:
            mess = client.recv(2048).decode('utf-8')
            if not mess:
                print("\033[31mServer đã ngắt kết nối\033[0m")
                break
            '''Sử dụng sys.stdout thay vì print vì print
            vì print sẽ tự thêm \n'''
            sys.stdout.write('\r' + ' ' * 40 + '\r')
            sys.stdout.write(mess)
            sys.stdout.write("\n")
            sys.stdout.write("\033[1;32mBạn: \033[0m")
            sys.stdout.flush()
        except:
            print("\033[31mServer đã ngắt kết nối\033[0m")
            client.close()
            break

#Hàm gửi tin nhắn
def send(client, nickname):
    while start:
        try:
            sys.stdout.write("\033[1;32mBạn: \033[0m")
            sys.stdout.flush()
            mess = input()
            if not mess.strip():
            #Bỏ qua dòng trống
                continue            
            if mess == "/clear":
            # Xóa màn hình hệ điều hành Window
                os.system('cls')
                continue
            client.sendall(mess.encode('utf-8'))
            #Kiểm tra tin nhắn có bye thì ngắt kết nối
            if "bye" in mess.lower():
                print("\033[31mBạn đã ngắt kết nối\033[0m")
                client.close()
                break
        except:
            print("\033[31mBạn đã ngắt kết nối\033[0m")
            client.close()
            break

def main():
    #Tạo socket cho client
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))
   
   #Sau khi tạo kết nối với server thì tạo nickname
    try:
        #Vòng lặp cho đến ki nickname phù hợp mới break
        while True:
            mess_server = client.recv(1024).decode('utf-8')
            if not mess_server:
                print("\033[31m[ERROR] Không nhận được dữ liệu từ server.\033[0m")
                client.close()
                return
            print(mess_server)

            nickname = input("\033[1mNhập nickname: \033[0m")
            client.sendall(nickname.encode('utf-8'))

            mess_server_reply = client.recv(1024).decode('utf-8')
            if "OKay" in mess_server_reply:
                print("\033[1mNickname hợp lệ!\033[0m")
                print("\033[1mBạn đã tham gia trò chuyện\033[0m")
                print("\033[1mNhập /help để xem danh sách các chức năng hỗ trợ\033[0m")
                break
            else:
                print(mess_server_reply)
    except:
        print("\033[31m[ERROR]\033[0m")
        client.close()

    #Sau khi có nickname thì tạo luồng receive và send để nhận gửi tin nhắn
    thread_recv = threading.Thread(target=receive, args=(client,), daemon=True)
    thread_send = threading.Thread(target=send, args=(client,nickname))
    thread_recv.start()
    thread_send.start()

if __name__ == "__main__":
    main()
