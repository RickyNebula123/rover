#include "client_functions.h"
client_info *generate_client_info(int *socket, struct sockaddr_in *CLIENT_){
    client_info* foo = (client_info *)malloc(sizeof(client_info));
    foo->ADDR_ = (*CLIENT_);    // Might need to use memcpy() here
    foo->socket_ = *(socket);
    return foo;
}

void fill_sock_addr_in(struct sockaddr_in *t, char *ip, in_port_t port){
    t->sin_family = AF_INET;
    t->sin_port = htons(port);
    inet_pton(AF_INET, ip, &(t->sin_addr.s_addr));
}

int establish_rover_connection(char *rover_address, in_port_t port_){
    int rover_socket = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in rover_server_info;
    fill_sock_addr_in(&rover_server_info, rover_address, port_);


    char ra[INET_ADDRSTRLEN];
    inet_ntop(AF_INET, &(rover_server_info.sin_addr.s_addr), ra, INET_ADDRSTRLEN);
    printf("Rover address: %s\n", ra);

    if(connect(rover_socket, (struct sockaddr *) &rover_server_info, sizeof(rover_server_info)) == -1){
        printf("Error connecting to rover: %s\n", strerror(errno));
    }
    return rover_socket;
}

char* get_ip(client_info *foo){ // Returns IP address in presentation style "xxx.xxx.xxx.xxx"
    return inet_ntoa((foo->ADDR_).sin_addr);
}

void announce_client_connection(char *IP_){
    printf("Client connection from: %s\n", IP_);
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

void *handle_connection(client_info * CLIENT_, int rover_socket){
    int BUFF_SIZE = 64;
    int recvd = 0;

    char msg[BUFF_SIZE];
    char *ip_ = get_ip(CLIENT_);
    announce_client_connection(ip_);

    while(1){
        printf("Waiting for message...\n");
        recvd = read_in(CLIENT_->socket_, msg, BUFF_SIZE);
        printf("Message received: %s\n", msg);
        printf("Message length (strlen): %lu\n", strlen(msg));
        printf("Message length (recvd): %d\n", recvd);
        if(!recvd){
            printf("Connection closed: %s\n", ip_);
            break;
        }
        send(rover_socket, msg, recvd, 0); // Forward message to rover
    }
    free(CLIENT_);
}
