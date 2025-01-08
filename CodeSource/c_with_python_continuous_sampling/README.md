### 1、为了在C中解析JSON数据，需要[**cJSON**](https://github.com/DaveGamble/cJSON)库

```
git clone https://github.com/DaveGamble/cJSON.git
cd cJSON
mkdir build
cd build
cmake ..
make
sudo make install

```

### 2、可能报错

./client: error while loading shared libraries: libcjson.so.1: cannot open shared object file: No such file or directory

需要导入libcjson.so的库地址 默认安装在local下的lib 需要手动添加

export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

### 3、编译

gcc -o client client.c -lcjson
