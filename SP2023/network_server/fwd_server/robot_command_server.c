#include "client_functions.h"
#include "server_functions.h"

int main(){
    int QUEUE = 2; // Only room for 2 addresses, Web Server and Rover
    in_addr_t  ADDR_ = htonl(INADDR_ANY);
    in_port_t  PORT_ = htons(5555);

    char *rover_address = "192.168.1.223";   // Use when connected to home network 
    char *rover_iphone  = "172.20.10.6";     // Use when connected on phone
    in_port_t rover_port_= 4422;

    int rover_socket = establish_rover_connection(rover_iphone, rover_port_); // Create socket to Rover
    int server_      = spin_up_server(ADDR_, PORT_, QUEUE);                   // Create server that listens for commands to forward to Rover
    
    server_online(server_, rover_socket); // Starts listening
    return 0;
}