################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Windows.c \
../commstr.c \
../dvr_core.c \
../dvr_lowlayerinterface.c \
../dvr_sockserver.c \
../vk_bin2text.c \
../vk_daqoutput.c \
../vk_daqsetting.c \
../vk_default.c \
../vk_factory.c \
../vk_io.c \
../vk_nptrig.c \
../vk_readblock.c \
../vk_sdfile.c \
../vk_upgrade.c \
../vk_versionhistory.c 

C_DEPS += \
./Windows.d \
./commstr.d \
./dvr_core.d \
./dvr_lowlayerinterface.d \
./dvr_sockserver.d \
./vk_bin2text.d \
./vk_daqoutput.d \
./vk_daqsetting.d \
./vk_default.d \
./vk_factory.d \
./vk_io.d \
./vk_nptrig.d \
./vk_readblock.d \
./vk_sdfile.d \
./vk_upgrade.d \
./vk_versionhistory.d 

OBJS += \
./Windows.o \
./commstr.o \
./dvr_core.o \
./dvr_lowlayerinterface.o \
./dvr_sockserver.o \
./vk_bin2text.o \
./vk_daqoutput.o \
./vk_daqsetting.o \
./vk_default.o \
./vk_factory.o \
./vk_io.o \
./vk_nptrig.o \
./vk_readblock.o \
./vk_sdfile.o \
./vk_upgrade.o \
./vk_versionhistory.o 


# Each subdirectory must supply rules for building sources it contributes
%.o: ../%.c subdir.mk
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C Compiler'
	gcc -O0 -g3 -Wall -c -fmessage-length=0 -isystem ../ -fPIC -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


clean: clean--2e-

clean--2e-:
	-$(RM) ./Windows.d ./Windows.o ./commstr.d ./commstr.o ./dvr_core.d ./dvr_core.o ./dvr_lowlayerinterface.d ./dvr_lowlayerinterface.o ./dvr_sockserver.d ./dvr_sockserver.o ./vk_bin2text.d ./vk_bin2text.o ./vk_daqoutput.d ./vk_daqoutput.o ./vk_daqsetting.d ./vk_daqsetting.o ./vk_default.d ./vk_default.o ./vk_factory.d ./vk_factory.o ./vk_io.d ./vk_io.o ./vk_nptrig.d ./vk_nptrig.o ./vk_readblock.d ./vk_readblock.o ./vk_sdfile.d ./vk_sdfile.o ./vk_upgrade.d ./vk_upgrade.o ./vk_versionhistory.d ./vk_versionhistory.o

.PHONY: clean--2e-

