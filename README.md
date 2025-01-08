## 任务分解

### 1、Python代码理解整理和注释
```
问题一：数据采集和模型推理需要解耦
问题二：模型推理及后处理耗时需要控制在256ms以内
```

### 2、VK70xNMC_DAQ2.dll 从C源码编译成Linux下的so库
```
备注：源码需要对应的lubancat编译环境编译成对应的so，该so理论上python也可以调用
```

### 3、分离采集代码，转换成C语言

### 4、C语言RPC调用python代码进行模型推理和存入IoTDB

## 计划

### 1、鲁班猫烧写ubuntu22.04LTS

[3. 系统镜像烧录 — 快速使用手册—基于LubanCat-RK356x系列板卡 文档](https://doc.embedfire.com/linux/rk356x/quick_start/zh/latest/quick_start/flash_img/flash_img.html)

### 2、VK70xNMC_DAQ2.dll -> VK70xNMC_DAQ2.so

    需要VK70xNMC_DAQ2.c（已提供，makefile 确认要加上编译选型 -fPIC -shared）

### 3、鲁班猫安装IoTDB数据库
```
备注：iotdb装在本机上，实际场景中，客户有自己的db，我们这里模拟出和db进行交互的过程即可，发送约定的json格式字符串到iotdb
```

### 4、实现鲁班猫下运行python采集数据并存入IoTDB
```
上板实现的功能：采集数据->预处理->模型推理->整合结果发送json字符串到iotdb
```

### 5、实现C的数据采集功能
```
先用python调通，证明编译出的so库可用，再转成c语言实现
```

### 6、实现C的调用python推理功能
```
需要先学习mfcc函数对应的具体实现过程
```

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
step1：DAQ 快速使用指引 v1.3 配置以太网ip等 （先本机上调试好采集卡，再移植到鲁班猫）
step2：VK_DAQ testing suit - VK701N-SD v2 测试demo，测试采集卡是否正常工作（本机上调试，再移植到鲁班猫）
step3：采集卡正常工作，默认ip是192.168.1.199，本机是192.168.1.188，如果需要移植，鲁班猫需要修改ip，或者利用工具修改采集卡的ip，令采集卡和鲁班猫能正常工作
step4：运行现有的python demo时，可能会有依赖库的版本问题，需要统一，安装虚拟环境或适配
```

```
# 获取当前 DAQ 的句柄和 IP 地址
print("获取当前 DAQ 的句柄和 IP 地址...")
result = GetConnectedClientHandle(deviceNo, byref(curHandle), ipAdr)
```
