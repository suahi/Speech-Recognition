################################################################################
# sources.mk - 定义要编译的源文件和生成的对象文件
################################################################################

# C 源文件列表
C_SRCS := \
    src/commstr.c \
    src/dvr_core.c \
    src/dvr_lowlayerinterface.c \
    src/vk_daqoutput.c \
    src/vk_default.c \
    src/vk_io.c \
    src/vk_readblock.c \
    src/vk_upgrade.c \
    src/Windows.c \
    src/dvr_sockserver.c \
    src/vk_bin2text.c \
    src/vk_daqsetting.c \
    src/vk_factory.c \
    src/vk_nptrig.c \
    src/vk_sdfile.c \
    src/vk_versionhistory.c

# 生成对象文件列表（假设所有对象文件都放在 build/x86/ 目录中）
OBJS := \
    build/x86/commstr.o \
    build/x86/dvr_core.o \
    build/x86/dvr_lowlayerinterface.o \
    build/x86/vk_daqoutput.o \
    build/x86/vk_default.o \
    build/x86/vk_io.o \
    build/x86/vk_readblock.o \
    build/x86/vk_upgrade.o \
    build/x86/Windows.o \
    build/x86/dvr_sockserver.o \
    build/x86/vk_bin2text.o \
    build/x86/vk_daqsetting.o \
    build/x86/vk_factory.o \
    build/x86/vk_nptrig.o \
    build/x86/vk_sdfile.o \
    build/x86/vk_versionhistory.o

# 编译选项
CFLAGS += -fPIC -O2 -Wall -I./include
