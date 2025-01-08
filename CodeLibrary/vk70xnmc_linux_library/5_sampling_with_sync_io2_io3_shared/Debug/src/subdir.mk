################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../src/5_sampling_with_sync_io2_io3_shared.c 

C_DEPS += \
./src/5_sampling_with_sync_io2_io3_shared.d 

OBJS += \
./src/5_sampling_with_sync_io2_io3_shared.o 


# Each subdirectory must supply rules for building sources it contributes
src/%.o: ../src/%.c src/subdir.mk
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C Compiler'
	gcc -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


clean: clean-src

clean-src:
	-$(RM) ./src/5_sampling_with_sync_io2_io3_shared.d ./src/5_sampling_with_sync_io2_io3_shared.o

.PHONY: clean-src

