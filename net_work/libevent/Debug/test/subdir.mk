################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
O_SRCS += \
../test/bench.o \
../test/regress.gen.o \
../test/regress.o \
../test/regress_dns.o \
../test/regress_http.o \
../test/regress_rpc.o \
../test/test-eof.o \
../test/test-init.o \
../test/test-time.o \
../test/test-weof.o 

C_SRCS += \
../test/bench.c \
../test/regress.c \
../test/regress.gen.c \
../test/regress_dns.c \
../test/regress_http.c \
../test/regress_rpc.c \
../test/test-eof.c \
../test/test-init.c \
../test/test-time.c \
../test/test-weof.c 

OBJS += \
./test/bench.o \
./test/regress.o \
./test/regress.gen.o \
./test/regress_dns.o \
./test/regress_http.o \
./test/regress_rpc.o \
./test/test-eof.o \
./test/test-init.o \
./test/test-time.o \
./test/test-weof.o 

C_DEPS += \
./test/bench.d \
./test/regress.d \
./test/regress.gen.d \
./test/regress_dns.d \
./test/regress_http.d \
./test/regress_rpc.d \
./test/test-eof.d \
./test/test-init.d \
./test/test-time.d \
./test/test-weof.d 


# Each subdirectory must supply rules for building sources it contributes
test/%.o: ../test/%.c
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C Compiler'
	gcc -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o"$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


