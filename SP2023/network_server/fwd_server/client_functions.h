#ifndef CLIENT_FUNCTIONS
#define CLIENT_FUNCTIONS
#include <arpa/inet.h>
#include <errno.h>
#include <pthread.h>    // For future expandability
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct{
    struct sockaddr_in ADDR_;
    int socket_;
}client_info;
char *get_ip(client_info*);
client_info* generate_client_info(int *, struct sockaddr_in *);
int establish_rover_connection(char *, in_port_t);
int read_in(int, char *, int);
void announce_client_connection(char *);
void *handle_connection(client_info *, int);

#endif // CLIENT_FUNCTIONS