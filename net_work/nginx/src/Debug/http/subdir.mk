################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../http/ngx_http.c \
../http/ngx_http_busy_lock.c \
../http/ngx_http_copy_filter_module.c \
../http/ngx_http_core_module.c \
../http/ngx_http_file_cache.c \
../http/ngx_http_header_filter_module.c \
../http/ngx_http_parse.c \
../http/ngx_http_parse_time.c \
../http/ngx_http_postpone_filter_module.c \
../http/ngx_http_request.c \
../http/ngx_http_request_body.c \
../http/ngx_http_script.c \
../http/ngx_http_special_response.c \
../http/ngx_http_upstream.c \
../http/ngx_http_upstream_round_robin.c \
../http/ngx_http_variables.c \
../http/ngx_http_write_filter_module.c 

OBJS += \
./http/ngx_http.o \
./http/ngx_http_busy_lock.o \
./http/ngx_http_copy_filter_module.o \
./http/ngx_http_core_module.o \
./http/ngx_http_file_cache.o \
./http/ngx_http_header_filter_module.o \
./http/ngx_http_parse.o \
./http/ngx_http_parse_time.o \
./http/ngx_http_postpone_filter_module.o \
./http/ngx_http_request.o \
./http/ngx_http_request_body.o \
./http/ngx_http_script.o \
./http/ngx_http_special_response.o \
./http/ngx_http_upstream.o \
./http/ngx_http_upstream_round_robin.o \
./http/ngx_http_variables.o \
./http/ngx_http_write_filter_module.o 

C_DEPS += \
./http/ngx_http.d \
./http/ngx_http_busy_lock.d \
./http/ngx_http_copy_filter_module.d \
./http/ngx_http_core_module.d \
./http/ngx_http_file_cache.d \
./http/ngx_http_header_filter_module.d \
./http/ngx_http_parse.d \
./http/ngx_http_parse_time.d \
./http/ngx_http_postpone_filter_module.d \
./http/ngx_http_request.d \
./http/ngx_http_request_body.d \
./http/ngx_http_script.d \
./http/ngx_http_special_response.d \
./http/ngx_http_upstream.d \
./http/ngx_http_upstream_round_robin.d \
./http/ngx_http_variables.d \
./http/ngx_http_write_filter_module.d 


# Each subdirectory must supply rules for building sources it contributes
http/%.o: ../http/%.c
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C Compiler'
	gcc -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o"$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


