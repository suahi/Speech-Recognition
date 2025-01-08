################################################################################
# Automatically-generated file. Do not edit!
################################################################################

-include ../makefile.init

RM := rm -rf

# All of the sources participating in the build are defined here
-include sources.mk
-include src/subdir.mk
ifneq ($(MAKECMDGOALS),clean)
ifneq ($(strip $(C_DEPS)),)
-include $(C_DEPS)
endif
endif

-include ../makefile.defs

OPTIONAL_TOOL_DEPS := \
$(wildcard ../makefile.defs) \
$(wildcard ../makefile.init) \
$(wildcard ../makefile.targets) \


BUILD_ARTIFACT_NAME := 5_sampling_with_sync_io2_io3_static
BUILD_ARTIFACT_EXTENSION :=
BUILD_ARTIFACT_PREFIX :=
BUILD_ARTIFACT := $(BUILD_ARTIFACT_PREFIX)$(BUILD_ARTIFACT_NAME)$(if $(BUILD_ARTIFACT_EXTENSION),.$(BUILD_ARTIFACT_EXTENSION),)

# Add inputs and outputs from these tool invocations to the build variables 

# All Target
all: main-build

# Main-build Target
main-build: 5_sampling_with_sync_io2_io3_static

# Tool invocations
5_sampling_with_sync_io2_io3_static: $(OBJS) $(USER_OBJS) makefile $(OPTIONAL_TOOL_DEPS)
	@echo 'Building target: $@'
	@echo 'Invoking: GCC C Linker'
	gcc -L"/home/myir/vk70xnmc_for_linux/VK70XNMC_DAQ_STATIC/Debug" -o "5_sampling_with_sync_io2_io3_static" $(OBJS) $(USER_OBJS) $(LIBS) -lpthread -lVK70XNMC_DAQ_STATIC
	@echo 'Finished building target: $@'
	@echo ' '

# Other Targets
clean:
	-$(RM) 5_sampling_with_sync_io2_io3_static
	-@echo ' '

.PHONY: all clean dependents main-build

-include ../makefile.targets
