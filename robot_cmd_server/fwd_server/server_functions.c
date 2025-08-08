#include <stdlib.h>
#include "server_functions.h"
#include "client_functions.h"

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

void bind_server(int socket,  in_addr_t ADDR_, in_port_t PORT_){
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

int spin_up_server(in_addr_t ADDR_, in_port_t PORT_, int QUEUE){ // Create IPv4 socket, using TCP protocol.
    int server_socket = create_tcp_socket();
    bind_server(server_socket, ADDR_, PORT_);
    server_listen(server_socket, QUEUE);
    return server_socket;
}

int server_online(int server_, int rover_socket){
    printf("Server online\n");
    while(1){
        struct sockaddr_storage client_data;            // Initial capture of client data
        unsigned int addr_size = sizeof(client_data);
        int connection = accept(server_, (struct sockaddr *) &client_data, &addr_size);                 // Accept connection
        client_info *client_ = generate_client_info(&connection, (struct sockaddr_in*) &client_data);   // Create memory structure to pass onto pthread_t, (Contains socket and connection info)
        handle_connection(client_, rover_socket);    // Blocking call because no threads have been created yet
        printf("Waiting for a new connection...\n");

    }
}