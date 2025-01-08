// client.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <cjson/cJSON.h>

// 定义一个结构体来存储推理结果
typedef struct {
    long *predicted;
    double *confidences;
    int num_samples;
} InferenceResult;

// 函数声明
int send_raw_bytes(const char* host, int port, unsigned char* raw_bytes, uint32_t raw_len, InferenceResult* result);
void free_inference_result(InferenceResult* result);

int main() {
    // 示例音频数据
    unsigned char raw_bytes[] = {
        26, 43, 60, 77, 
        94, 111, 122, 139,
        156, 173, 190, 207
    };

    uint32_t raw_len = sizeof(raw_bytes);

    InferenceResult result = {0};

    // 服务器地址和端口
    const char* host = "127.0.0.1";
    int port = 65224;

    // 发送数据并接收结果
    if (send_raw_bytes(host, port, raw_bytes, raw_len, &result) != 0) {
        fprintf(stderr, "推理失败\n");
        return EXIT_FAILURE;
    }

    // 处理结果
    printf("推理结果:\n");
    for(int i = 0; i < result.num_samples; i++) {
        printf("样本 %d: Predicted = %ld, Confidence = %f\n", i+1, result.predicted[i], result.confidences[i]);
    }

    // 释放结果内存
    free_inference_result(&result);

    return EXIT_SUCCESS;
}

int send_raw_bytes(const char* host, int port, unsigned char* raw_bytes, uint32_t raw_len, InferenceResult* result) {
    int sock = 0;
    struct sockaddr_in serv_addr;
    if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        perror("socket 创建失败");
        return -1;
    }

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(port);

    // 将IPv4地址从文本转换为二进制形式
    if(inet_pton(AF_INET, host, &serv_addr.sin_addr)<=0) {
        perror("Invalid address/ Address not supported");
        close(sock);
        return -1;
    }

    if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        perror("连接失败");
        close(sock);
        return -1;
    }

    // 发送数据长度（4字节，网络字节序）
    uint32_t net_len = htonl(raw_len);
    if (send(sock, &net_len, sizeof(net_len), 0) != sizeof(net_len)) {
        perror("发送数据长度失败");
        close(sock);
        return -1;
    }

    // 发送实际数据
    if (send(sock, raw_bytes, raw_len, 0) != raw_len) {
        perror("发送数据失败");
        close(sock);
        return -1;
    }

    printf("已发送 %u bytes 数据\n", raw_len);

    // 接收结果长度（4字节）
    uint32_t result_len;
    ssize_t bytes_received = recv(sock, &result_len, sizeof(result_len), MSG_WAITALL);
    if (bytes_received != sizeof(result_len)) {
        perror("接收结果长度失败");
        close(sock);
        return -1;
    }
    result_len = ntohl(result_len);
    printf("将接收 %u bytes 结果数据\n", result_len);

    // 接收结果数据
    unsigned char* buffer = (unsigned char*)malloc(result_len + 1);
    if (!buffer) {
        fprintf(stderr, "内存分配失败\n");
        close(sock);
        return -1;
    }
    bytes_received = recv(sock, buffer, result_len, MSG_WAITALL);
    if (bytes_received != result_len) {
        perror("接收结果数据失败");
        free(buffer);
        close(sock);
        return -1;
    }
    buffer[result_len] = '\0'; // 确保字符串终止
    printf("已接收结果数据\n");

    // 解析JSON数据
    cJSON *json = cJSON_Parse((const char*)buffer);
    if (!json) {
        fprintf(stderr, "JSON解析失败\n");
        free(buffer);
        close(sock);
        return -1;
    }

    // 解析predicted数组
    cJSON *predicted_json = cJSON_GetObjectItem(json, "predicted");
    if (!cJSON_IsArray(predicted_json)) {
        fprintf(stderr, "predicted不是数组\n");
        cJSON_Delete(json);
        free(buffer);
        close(sock);
        return -1;
    }

    int predicted_count = cJSON_GetArraySize(predicted_json);
    result->predicted = (long*)malloc(sizeof(long) * predicted_count);
    result->confidences = (double*)malloc(sizeof(double) * predicted_count);
    result->num_samples = predicted_count;

    for(int i = 0; i < predicted_count; i++) {
        cJSON *item = cJSON_GetArrayItem(predicted_json, i);
        if (cJSON_IsNumber(item)) {
            result->predicted[i] = item->valuedouble;
        }
    }

    // 解析confidences数组
    cJSON *confidences_json = cJSON_GetObjectItem(json, "confidences");
    if (!cJSON_IsArray(confidences_json)) {
        fprintf(stderr, "confidences不是数组\n");
        cJSON_Delete(json);
        free(buffer);
        close(sock);
        return -1;
    }

    for(int i = 0; i < predicted_count; i++) {
        cJSON *item = cJSON_GetArrayItem(confidences_json, i);
        if (cJSON_IsNumber(item)) {
            result->confidences[i] = item->valuedouble;
        }
    }

    cJSON_Delete(json);
    free(buffer);
    close(sock);
    return 0;
}

void free_inference_result(InferenceResult* result) {
    if (result->predicted) {
        free(result->predicted);
        result->predicted = NULL;
    }
    if (result->confidences) {
        free(result->confidences);
        result->confidences = NULL;
    }
    result->num_samples = 0;
}
