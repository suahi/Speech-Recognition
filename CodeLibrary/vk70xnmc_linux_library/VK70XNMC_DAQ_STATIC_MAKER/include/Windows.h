/*
 * Windows.h
 *
 *  Created on: 2024年1月7日
 *      Author: arci
 */

#ifndef WINDOWS_H_
#define WINDOWS_H_

	#include <pthread.h>
	#include <stdint.h>
	#include <sys/ioctl.h>

	#define Sleep(n) usleep(n * 1000)
	#define WINAPI
	#define timeBeginPeriod(x)
	#define timeEndPeriod(x)
	#define stricmp strcasecmp
	#define _access access
	typedef pthread_t* HANDLE;
	typedef void *PVOID;
	typedef void * DWORD;
	typedef uint32_t UINT32;
	typedef uint64_t ULONG;
	uint32_t GetFileAttributes(const char* lpFileName);
	int CreateDirectory(const char* lpFileName, void *attr);
	HANDLE CreateThread(void *reserve0, int reserve1, void *(*__start_routine)(void*), void *reserve2, int reserve3, void *reserve4);

#endif /* WINDOWS_H_ */
