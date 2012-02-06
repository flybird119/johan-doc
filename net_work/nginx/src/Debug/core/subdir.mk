################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../core/nginx.c \
../core/ngx_array.c \
../core/ngx_buf.c \
../core/ngx_conf_file.c \
../core/ngx_connection.c \
../core/ngx_cpuinfo.c \
../core/ngx_crc32.c \
../core/ngx_cycle.c \
../core/ngx_file.c \
../core/ngx_hash.c \
../core/ngx_inet.c \
../core/ngx_list.c \
../core/ngx_log.c \
../core/ngx_md5.c \
../core/ngx_murmurhash.c \
../core/ngx_open_file_cache.c \
../core/ngx_output_chain.c \
../core/ngx_palloc.c \
../core/ngx_parse.c \
../core/ngx_queue.c \
../core/ngx_radix_tree.c \
../core/ngx_rbtree.c \
../core/ngx_regex.c \
../core/ngx_resolver.c \
../core/ngx_shmtx.c \
../core/ngx_slab.c \
../core/ngx_spinlock.c \
../core/ngx_string.c \
../core/ngx_times.c 

OBJS += \
./core/nginx.o \
./core/ngx_array.o \
./core/ngx_buf.o \
./core/ngx_conf_file.o \
./core/ngx_connection.o \
./core/ngx_cpuinfo.o \
./core/ngx_crc32.o \
./core/ngx_cycle.o \
./core/ngx_file.o \
./core/ngx_hash.o \
./core/ngx_inet.o \
./core/ngx_list.o \
./core/ngx_log.o \
./core/ngx_md5.o \
./core/ngx_murmurhash.o \
./core/ngx_open_file_cache.o \
./core/ngx_output_chain.o \
./core/ngx_palloc.o \
./core/ngx_parse.o \
./core/ngx_queue.o \
./core/ngx_radix_tree.o \
./core/ngx_rbtree.o \
./core/ngx_regex.o \
./core/ngx_resolver.o \
./core/ngx_shmtx.o \
./core/ngx_slab.o \
./core/ngx_spinlock.o \
./core/ngx_string.o \
./core/ngx_times.o 

C_DEPS += \
./core/nginx.d \
./core/ngx_array.d \
./core/ngx_buf.d \
./core/ngx_conf_file.d \
./core/ngx_connection.d \
./core/ngx_cpuinfo.d \
./core/ngx_crc32.d \
./core/ngx_cycle.d \
./core/ngx_file.d \
./core/ngx_hash.d \
./core/ngx_inet.d \
./core/ngx_list.d \
./core/ngx_log.d \
./core/ngx_md5.d \
./core/ngx_murmurhash.d \
./core/ngx_open_file_cache.d \
./core/ngx_output_chain.d \
./core/ngx_palloc.d \
./core/ngx_parse.d \
./core/ngx_queue.d \
./core/ngx_radix_tree.d \
./core/ngx_rbtree.d \
./core/ngx_regex.d \
./core/ngx_resolver.d \
./core/ngx_shmtx.d \
./core/ngx_slab.d \
./core/ngx_spinlock.d \
./core/ngx_string.d \
./core/ngx_times.d 


# Each subdirectory must supply rules for building sources it contributes
core/%.o: ../core/%.c
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C Compiler'
	gcc -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o"$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


