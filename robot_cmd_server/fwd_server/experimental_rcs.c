#include <arpa/inet.h>
#include <pthread.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <sys/socket.h>

typedef struct{
    struct sockaddr_in ADDR_;
    int socket_;
}client_info;
client_info *generate_client_info(int *socket, struct sockaddr_in *CLIENT_){
    client_info* foo = (client_info *)malloc(sizeof(client_info));
    foo->ADDR_ = (*CLIENT_);    // Might need to use memcpy() here
    foo->socket_ = *(socket);
    return foo;
}
char* get_ip(client_info *foo){ // Returns IP address in presentation style "xxx.xxx.xxx.xxx"
    return inet_ntoa((foo->ADDR_).sin_addr);
}
void announce_client_connection(char *IP_){
    printf("Client connection from: %s\n", IP_);

}
void error_handle(char *msg){
    printf("%s", msg);
    exit(1);
}
int create_tcp_socket(){
    int socket_ = socket(AF_INET, SOCK_STREAM, 0);
    if(socket_ == -1){
        error_handle("Error: Unable to create tcp socket.");
    }
    return socket_;
}
void bind_server(int socket,  uint32_t ADDR_, uint16_t PORT_){
    struct sockaddr_in server_info;
    server_info.sin_family = AF_INET;
    server_info.sin_port = PORT_;
    server_info.sin_addr.s_addr = ADDR_;

    int reuse = 1;
    if(setsockopt(socket, SOL_SOCKET, SO_REUSEADDR, (char *) &reuse, sizeof(int)) == -1){
        error_handle("Unable to reuse socket.");
    }
    if(bind(socket, (struct sockaddr *) &server_info, sizeof(server_info)) == -1){
        error_handle("Unable to bind server socket.");
    }
}
void server_listen(int server_, int QUEUE){
    if(listen(server_, QUEUE) == -1){
        error_handle("Unable to listen on specified port.\n");
    }
}
int spin_up_server(uint32_t ADDR_, uint16_t PORT_, int QUEUE){ // Create IPv4 socket, using TCP protocol.
    int server_socket = create_tcp_socket();
    bind_server(server_socket, ADDR_, PORT_);
    server_listen(server_socket, QUEUE);
    return server_socket;
}
int read_in(int client_socket, char* buf, int len){
    char *s = buf;  // Points to the external buffer
    int slen = len; // Length of buf

    int c = recv(client_socket, s, slen, 0);
    while((c > 0) && s[c-1] != '\0'){
        s += c; // Move the pointer to new blank value.
        slen -= c;
        c = recv(client_socket, s, slen, 0); // Keep reading messages if necessary
    }
    return c;
}
void *handle_connection(client_info * CLIENT_){
    int BUFF_SIZE = 64;
    int recvd = 0;

    char msg[BUFF_SIZE];
    char *ip_ = get_ip(CLIENT_);

    announce_client_connection(ip_);
    while(1){
    printf("Waiting for message...\n");
    recvd = read_in(CLIENT_->socket_, msg, BUFF_SIZE);
    printf("Message received: %s\n", msg);
    if(!recvd){
        printf("Connection closed: %s\n", ip_);
        break;
    }
    }
    free(CLIENT_);
}
int server_online(int server_){
   while(1){
        struct sockaddr_storage client_data;            // Initial capture of client data
        unsigned int addr_size = sizeof(client_data);
        int connection = accept(server_, (struct sockaddr *) &client_data, &addr_size);                 // Accept connection
        client_info *client_ = generate_client_info(&connection, (struct sockaddr_in*) &client_data);   // Create memory structure to pass onto pthread_t, (Contains socket and connection info)
        handle_connection(client_);    // Blocking call because no threads have been created yet
        printf("Waiting for a new connection...\n");

    }
}

int main(){
    int QUEUE = 2; // Only room for 2 addresses, Web Server and Rover
    in_addr_t ADDR_ = htonl(INADDR_ANY);
    in_port_t PORT_    = htons(5555);

    int server_ = spin_up_server(ADDR_, PORT_, QUEUE);
    server_online(server_); // Starts listening
    return 0;
}

