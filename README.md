## 任务分解

### 1、Python代码理解整理和注释

### 2、VK70xNMC_DAQ2.dll 从C源码编译成Linux下的so库

### 3、分离采集代码，转换成C语言

### 4、C语言RPC调用python代码进行模型推理和存入IoTDB

## 计划

### 1、鲁班猫烧写ubuntu22.04LTS

[3. 系统镜像烧录 — 快速使用手册—基于LubanCat-RK356x系列板卡 文档](https://doc.embedfire.com/linux/rk356x/quick_start/zh/latest/quick_start/flash_img/flash_img.html)

### 2、VK70xNMC_DAQ2.dll -> VK70xNMC_DAQ2.so

    需要VK70xNMC_DAQ2.c

### 3、鲁班猫安装IoTDB数据库

### 4、实现鲁班猫下运行python采集数据并存入IoTDB

### 5、实现C的数据采集功能

### 6、实现C的调用python推理功能

```
#保留 
#对采样数据进行推理处理
predicted, confidences, raw_datas, real, imaginary = inference(databuff_element)
# 将推理结果存入 IoT 数据库
in_iotdb(predicted, confidences, timestamp_element, raw_datas, real, imaginary)
```

## 已知问题

### 1、换一台电脑可能就无法读取到IP地址

```
# 获取当前 DAQ 的句柄和 IP 地址
print("获取当前 DAQ 的句柄和 IP 地址...")
result = GetConnectedClientHandle(deviceNo, byref(curHandle), ipAdr)
```
