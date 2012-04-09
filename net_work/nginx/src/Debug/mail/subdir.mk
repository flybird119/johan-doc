################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../mail/ngx_mail.c \
../mail/ngx_mail_auth_http_module.c \
../mail/ngx_mail_core_module.c \
../mail/ngx_mail_handler.c \
../mail/ngx_mail_imap_handler.c \
../mail/ngx_mail_imap_module.c \
../mail/ngx_mail_parse.c \
../mail/ngx_mail_pop3_handler.c \
../mail/ngx_mail_pop3_module.c \
../mail/ngx_mail_proxy_module.c \
../mail/ngx_mail_smtp_handler.c \
../mail/ngx_mail_smtp_module.c \
../mail/ngx_mail_ssl_module.c 

OBJS += \
./mail/ngx_mail.o \
./mail/ngx_mail_auth_http_module.o \
./mail/ngx_mail_core_module.o \
./mail/ngx_mail_handler.o \
./mail/ngx_mail_imap_handler.o \
./mail/ngx_mail_imap_module.o \
./mail/ngx_mail_parse.o \
./mail/ngx_mail_pop3_handler.o \
./mail/ngx_mail_pop3_module.o \
./mail/ngx_mail_proxy_module.o \
./mail/ngx_mail_smtp_handler.o \
./mail/ngx_mail_smtp_module.o \
./mail/ngx_mail_ssl_module.o 

C_DEPS += \
./mail/ngx_mail.d \
./mail/ngx_mail_auth_http_module.d \
./mail/ngx_mail_core_module.d \
./mail/ngx_mail_handler.d \
./mail/ngx_mail_imap_handler.d \
./mail/ngx_mail_imap_module.d \
./mail/ngx_mail_parse.d \
./mail/ngx_mail_pop3_handler.d \
./mail/ngx_mail_pop3_module.d \
./mail/ngx_mail_proxy_module.d \
./mail/ngx_mail_smtp_handler.d \
./mail/ngx_mail_smtp_module.d \
./mail/ngx_mail_ssl_module.d 


# Each subdirectory must supply rules for building sources it contributes
mail/%.o: ../mail/%.c
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C Compiler'
	gcc -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o"$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


