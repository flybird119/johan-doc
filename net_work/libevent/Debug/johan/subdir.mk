################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../johan/demo.c \
../johan/time-test.c 

OBJS += \
./johan/demo.o \
./johan/time-test.o 

C_DEPS += \
./johan/demo.d \
./johan/time-test.d 


# Each subdirectory must supply rules for building sources it contributes
johan/%.o: ../johan/%.c
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C Compiler'
	gcc -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o"$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


