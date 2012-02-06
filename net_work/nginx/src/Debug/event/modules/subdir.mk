################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../event/modules/ngx_aio_module.c \
../event/modules/ngx_devpoll_module.c \
../event/modules/ngx_epoll_module.c \
../event/modules/ngx_eventport_module.c \
../event/modules/ngx_kqueue_module.c \
../event/modules/ngx_poll_module.c \
../event/modules/ngx_rtsig_module.c \
../event/modules/ngx_select_module.c \
../event/modules/ngx_win32_select_module.c 

OBJS += \
./event/modules/ngx_aio_module.o \
./event/modules/ngx_devpoll_module.o \
./event/modules/ngx_epoll_module.o \
./event/modules/ngx_eventport_module.o \
./event/modules/ngx_kqueue_module.o \
./event/modules/ngx_poll_module.o \
./event/modules/ngx_rtsig_module.o \
./event/modules/ngx_select_module.o \
./event/modules/ngx_win32_select_module.o 

C_DEPS += \
./event/modules/ngx_aio_module.d \
./event/modules/ngx_devpoll_module.d \
./event/modules/ngx_epoll_module.d \
./event/modules/ngx_eventport_module.d \
./event/modules/ngx_kqueue_module.d \
./event/modules/ngx_poll_module.d \
./event/modules/ngx_rtsig_module.d \
./event/modules/ngx_select_module.d \
./event/modules/ngx_win32_select_module.d 


# Each subdirectory must supply rules for building sources it contributes
event/modules/%.o: ../event/modules/%.c
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C Compiler'
	gcc -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o"$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


