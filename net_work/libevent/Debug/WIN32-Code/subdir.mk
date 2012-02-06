################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../WIN32-Code/win32.c 

OBJS += \
./WIN32-Code/win32.o 

C_DEPS += \
./WIN32-Code/win32.d 


# Each subdirectory must supply rules for building sources it contributes
WIN32-Code/%.o: ../WIN32-Code/%.c
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C Compiler'
	gcc -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o"$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


