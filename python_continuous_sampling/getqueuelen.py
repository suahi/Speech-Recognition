def getqueuelen(queue):
    arraylen = 0
    for array in queue.queue:
        arraylen += len(array)
    return arraylen