#ifndef SERVER_FUNCTIONS
#define SERVER_FUNCTIONS
#include <arpa/inet.h>
#include <stdio.h>
#include <sys/socket.h>
#include <stdint.h>

void error_handle(char *);
void bind_server(int, in_addr_t, in_port_t);
void server_listen(int, int);
int create_tcp_socket();
int spin_up_server(in_addr_t, in_port_t, int);
int server_online(int, int);

#endif // SERVER_FUNCTIONS