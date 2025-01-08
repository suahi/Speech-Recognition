/*
 * Windows.c
 *
 *  Created on: 2023年12月22日
 *      Author: arci
 */

#include <Windows.h>
#include <pthread.h>
#include <stdint.h>
#include <unistd.h>
//typedef unsigned long int pthread_t;
//extern int pthread_create (pthread_t *__restrict __newthread,
//			   const pthread_attr_t *__restrict __attr,
//			   void *(*__start_routine) (void *),
//			   void *__restrict __arg) __THROWNL __nonnull ((1, 3));
HANDLE CreateThread(void *reserve0, int reserve1, void *(*__start_routine)(void*), void *reserve2, int reserve3, void *reserve4)
{
	HANDLE thread_id = malloc(sizeof (pthread_t));
	int result = pthread_create(thread_id, NULL, __start_routine, NULL);
	if (result != 0)
	{
		free(thread_id);
		thread_id = NULL;
	}
	return thread_id;
}

uint32_t GetFileAttributes(const char* lpFileName)
{
	//检查目录是否存在
	if (access(lpFileName, F_OK) == -1)
	{
		///目录不存在，创建目录
		//if (mkdir(lpFileName, 0777);
		return 0xFFFFFFFF;
	}
	return 0;
}

int CreateDirectory(const char* lpFileName, void *attr)
{
	return mkdir(lpFileName, 0777);
}
