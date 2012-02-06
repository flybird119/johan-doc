################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
O_SRCS += \
../buffer.o \
../epoll.o \
../evbuffer.o \
../evdns.o \
../event.o \
../event_tagging.o \
../evrpc.o \
../evutil.o \
../http.o \
../log.o \
../poll.o \
../select.o \
../signal.o \
../strlcpy.o 

C_SRCS += \
../buffer.c \
../devpoll.c \
../epoll.c \
../epoll_sub.c \
../evbuffer.c \
../evdns.c \
../event.c \
../event_tagging.c \
../evport.c \
../evrpc.c \
../evutil.c \
../http.c \
../kqueue.c \
../log.c \
../poll.c \
../select.c \
../signal.c \
../strlcpy.c 

OBJS += \
./buffer.o \
./devpoll.o \
./epoll.o \
./epoll_sub.o \
./evbuffer.o \
./evdns.o \
./event.o \
./event_tagging.o \
./evport.o \
./evrpc.o \
./evutil.o \
./http.o \
./kqueue.o \
./log.o \
./poll.o \
./select.o \
./signal.o \
./strlcpy.o 

C_DEPS += \
./buffer.d \
./devpoll.d \
./epoll.d \
./epoll_sub.d \
./evbuffer.d \
./evdns.d \
./event.d \
./event_tagging.d \
./evport.d \
./evrpc.d \
./evutil.d \
./http.d \
./kqueue.d \
./log.d \
./poll.d \
./select.d \
./signal.d \
./strlcpy.d 


# Each subdirectory must supply rules for building sources it contributes
%.o: ../%.c
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C Compiler'
	gcc -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o"$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


