################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../http/modules/perl/ngx_http_perl_module.c 

OBJS += \
./http/modules/perl/ngx_http_perl_module.o 

C_DEPS += \
./http/modules/perl/ngx_http_perl_module.d 


# Each subdirectory must supply rules for building sources it contributes
http/modules/perl/%.o: ../http/modules/perl/%.c
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C Compiler'
	gcc -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o"$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


