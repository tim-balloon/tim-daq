/*

Gyroscope Parser in C
The functions init_gyro_port() and read_gyro() can be used in Python scripts using ctypes.
(See ctypes_test.py)

Compile
gcc CSerialParser.c -o CSerialParser

*/


// C library headers
#include <stdio.h>

#include <stdlib.h>

#include <string.h>

// Linux headers
#include <fcntl.h> // Contains file controls like O_RDWR

#include <errno.h> // Error integer and strerror() function

#include <termios.h> // Contains POSIX terminal control definitions

#include <unistd.h> // write(), read(), close()


//Struct TUPLE with gyroscope data
typedef struct {
  float x_data;
  float y_data;
  float z_data;
  int seq_data;
  int temp_data;

}
TUPLE;

//Initializations
TUPLE * read_gyro(int ser);
void free_tuple(TUPLE * t);
int init_gyro_port();

int main(char ** argv, int argc) {
  
}



int init_gyro_port() {
  /*
  Opens the gyroscope port and sets serial flags. 
  Returns gyroscope port number.
  */
  

  // Open the serial port. Change device path as needed (currently set to an standard FTDI USB-UART cable type device)
  int serial_port = open("/dev/ttyUSB1", O_RDONLY | O_NDELAY);
  
  // Create new termios struc, we call it 'tty' for convention
  struct termios tty;

  // Read in existing settings, and handle any error
  if (tcgetattr(serial_port, & tty) != 0) {
    printf("Error %i from tcgetattr: %s\n", errno, strerror(errno));

  }

  tty.c_cflag &= ~PARENB; // Clear parity bit, disabling parity (most common)
  tty.c_cflag &= ~CSTOPB; // Clear stop field, only one stop bit used in communication (most common)
  tty.c_cflag &= ~CSIZE; // Clear all bits that set the data size 
  tty.c_cflag |= CS8; // 8 bits per byte (most common)
  tty.c_cflag &= ~CRTSCTS; // Disable RTS/CTS hardware flow control (most common)
  tty.c_cflag |= CREAD | CLOCAL; // Turn on READ & ignore ctrl lines (CLOCAL = 1)

  tty.c_lflag &= ~ICANON;
  tty.c_lflag &= ~ECHO; // Disable echo
  tty.c_lflag &= ~ECHOE; // Disable erasure
  tty.c_lflag &= ~ECHONL; // Disable new-line echo
  tty.c_lflag &= ~ISIG; // Disable interpretation of INTR, QUIT and SUSP
  tty.c_iflag &= ~(IXON | IXOFF | IXANY); // Turn off s/w flow ctrl
  tty.c_iflag &= ~(IGNBRK | BRKINT | PARMRK | ISTRIP | INLCR | IGNCR | ICRNL); // Disable any special handling of received bytes

  tty.c_oflag &= ~OPOST; // Prevent special interpretation of output bytes (e.g. newline chars)
  tty.c_oflag &= ~ONLCR; // Prevent conversion of newline to carriage return/line feed


  tty.c_cc[VTIME] = 0; // Wait for up to 1s (10 deciseconds), returning as soon as any data is received.
  tty.c_cc[VMIN] = 0;

  // Set in/out baud rate to be 115200
  cfsetispeed( & tty, B115200);
  cfsetospeed( & tty, B115200);

  // Save tty settings, also checking for error
  if (tcsetattr(serial_port, TCSANOW, & tty) != 0) {
    printf("Error %i from tcsetattr: %s\n", errno, strerror(errno));
  
  }    
  //tcflush(serial_port, TCIOFLUSH); //Initial flush of serial buffer
  return serial_port; //Return serial port number
}




TUPLE * read_gyro(int ser) {
  /* param ser: gyroscope port number

  Reads from serial port, parses, and returns gyroscope XYZ, sequence number, and temperature
  
  */

  char read_buf[1]; 
  char read_byte[3];
  char const *header = "fe81ff55";
  char header_buf[128] = "";
  char sentence_buf[128] = "";

  int sentence_complete = 0;
  int reading_sentence = 0;

  while (sentence_complete == 0) {
    
    int num_bytes = read(ser, &read_buf, sizeof(read_buf)); //Reading from port (ser)

    // n is the number of bytes read. n may be 0 if no bytes were received, and can also be -1 to signal an error.
    if (num_bytes < 0) {
      printf("Error reading: %s", strerror(errno));
      break;
    }

    //Converting char to 'string'
    sprintf(read_byte, "%02x", (unsigned char) read_buf[0]);
    
    if (strstr(header_buf, header) != NULL) { //Check if header has appeared   
      reading_sentence = 1;
    }

    if (reading_sentence == 0) { //If header hasn't appeared yet
      strncat(header_buf, read_byte, 2); //Continue searching for header, concate read bytes
      //printf("%s\n", read_byte);
      //printf("header : %s\n", header_buf);
    } else { //Once header has been found

      if (strlen(sentence_buf) < 58) { //Keep going until sentence complete
        strncat(sentence_buf, read_byte, 2);
        //printf("%s\n", read_byte);
        //printf("sentence : %s\n", sentence_buf);
        //strcat(sentence_buf," "); //Spaces used as tokens for strtok
      } else {

        sentence_complete = 1; //Once sentence is complete, exit while loop

        //printf("%s\n", sentence_buf);
        
        TUPLE * r;
        //Allocating memory for the tuple
        r = malloc(sizeof(TUPLE));

        //Splitting sentence string using window position and lengths 
        //One character added to char array to accomodate terminate character 
        char x_raw[9] = "";
        u_int32_t x_int;
        float x;
        snprintf(x_raw, sizeof(x_raw), "%.*s", 8, sentence_buf); //XYZ values need float conversions
        sscanf(x_raw, "%x", & x_int); 
        x = * ((float * ) & x_int);

        char y_raw[9] = "";
        u_int32_t y_int;
        float y;
        snprintf(y_raw, sizeof(y_raw), "%.*s", 8, sentence_buf + 8);
        sscanf(y_raw, "%x", & y_int);
        y = * ((float * ) & y_int);

        char z_raw[9] = "";
        u_int32_t z_int;
        float z;
        snprintf(z_raw, sizeof(z_raw), "%.*s", 8, sentence_buf + 16);
        sscanf(z_raw, "%x", & z_int);
        z = * ((float * ) & z_int);

        char seq_num_raw[3] = "";
        int seq_num;
        snprintf(seq_num_raw, sizeof(seq_num_raw), "%.*s", 2, sentence_buf + 50);
        seq_num = (int) strtol(seq_num_raw, NULL, 16);

        char status_raw[3] = "";
        snprintf(status_raw, sizeof(status_raw), "%.*s", 2, sentence_buf + 48);

        char temp_raw[5] = "";
        int temp;
        snprintf(temp_raw, sizeof(temp_raw), "%.*s", 4, sentence_buf + 52);
        temp = (int) strtol(temp_raw, NULL, 16);

        printf("x: %s y: %s z: %s status: %s seq_num: %s temperature: %s\n", x_raw, y_raw, z_raw, status_raw, seq_num_raw, temp_raw);
        //printf("X: %.9f Y: %.9f Z:%.9f seq_num: %d status: %s temp: %d\n", x, y, z, seq_num, status_raw, temp);

        TUPLE read = {
          x,
          y,
          z,
          seq_num,
          temp
        };

        * r = read;

        //Reseting char arrays
        sentence_buf[0] = '\0';
        header_buf[0] = '\0';
        
        return r;
        //free(r); //Free from previous malloc 
      }
    }
  }
}


