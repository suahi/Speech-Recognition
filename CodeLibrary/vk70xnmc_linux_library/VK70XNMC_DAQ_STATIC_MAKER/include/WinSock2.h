/*
 * WinSock2.h
 *
 *  Created on: 2024年1月7日
 *      Author: arci
 */

#ifndef WINSOCK2_H_
#define WINSOCK2_H_

	#include <Windows.h>
	#include <sys/socket.h>
	#include <netinet/in.h>
	#include <errno.h>
	#define INVALID_SOCKET (-1)
	#define SOCKET_ERROR (-1)
	#define ioctlsocket ioctl
	#define closesocket close
	#define WSAGetLastError() errno
	typedef int SOCKET;
	typedef struct sockaddr_in SOCKADDR_IN;
	typedef struct sockaddr SOCKADDR;

#endif /* WINSOCK2_H_ */
