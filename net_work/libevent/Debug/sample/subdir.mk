################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
O_SRCS += \
../sample/event-test.o \
../sample/signal-test.o \
../sample/time-test.o 

C_SRCS += \
../sample/event-test.c \
../sample/signal-test.c \
../sample/time-test.c 

OBJS += \
./sample/event-test.o \
./sample/signal-test.o \
./sample/time-test.o 

C_DEPS += \
./sample/event-test.d \
./sample/signal-test.d \
./sample/time-test.d 


# Each subdirectory must supply rules for building sources it contributes
sample/%.o: ../sample/%.c
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C Compiler'
	gcc -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o"$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


