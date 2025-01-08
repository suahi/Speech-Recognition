################################################################################
# Makefile - 用于生成 libVK70XNMC_DAQ_SHARED.so 动态库
# Automatically-generated file. Do not edit!
################################################################################

-include ../makefile.init

RM := rm -rf

# All of the sources participating in the build are defined here
-include sources.mk
-include subdir.mk
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


BUILD_ARTIFACT_NAME := VK70XNMC_DAQ_SHARED
BUILD_ARTIFACT_EXTENSION := so
BUILD_ARTIFACT_PREFIX := lib
BUILD_ARTIFACT := $(BUILD_ARTIFACT_PREFIX)$(BUILD_ARTIFACT_NAME)$(if $(BUILD_ARTIFACT_EXTENSION),.$(BUILD_ARTIFACT_EXTENSION),)

# Compiler and Flags
CC := gcc
CXX := g++
CFLAGS += -fPIC -O2 -Wall -I./include
CPPFLAGS += -fPIC -O2 -Wall -I./include

# Add inputs and outputs from these tool invocations to the build variables 

# All Target
all: main-build

# Main-build Target
main-build: $(BUILD_ARTIFACT)

# Tool invocations
$(BUILD_ARTIFACT): $(OBJS) $(USER_OBJS) $(OPTIONAL_TOOL_DEPS)
	@echo 'Building target: $@'
	@echo 'Invoking: GCC C Linker'
	$(CC) -shared -o "$@" $(OBJS) $(USER_OBJS) $(LIBS)
	@echo 'Finished building target: $@'
	@echo ' '

# Compile C sources to object files
build/x86/%.o: src/%.c | build/x86
	@echo "Compiling $<..."
	$(CC) $(CFLAGS) -c $< -o $@

# Compile C++ sources to object files (如果有 C++ 源文件)
build/x86/%.o: src/%.cpp | build/x86
	@echo "Compiling $<..."
	$(CXX) $(CPPFLAGS) -c $< -o $@

# Create build directory
build/x86:
	@mkdir -p build/x86

# Other Targets
clean:
	-$(RM) $(BUILD_ARTIFACT)
	-$(RM) build/x86
	-@echo 'Clean complete.'

.PHONY: all clean dependents main-build

-include ../makefile.targets
