################################################################################
# Automatically-generated file. Do not edit!
################################################################################

-include ../makefile.init

RM := rm -rf

# All of the sources participating in the build are defined here
-include sources.mk
-include subdir.mk
-include os/unix/subdir.mk
-include misc/subdir.mk
-include mail/subdir.mk
-include http/subdir.mk
-include http/modules/perl/subdir.mk
-include http/modules/subdir.mk
-include event/subdir.mk
-include event/modules/subdir.mk
-include core/subdir.mk
-include objects.mk

ifneq ($(MAKECMDGOALS),clean)
ifneq ($(strip $(C_DEPS)),)
-include $(C_DEPS)
endif
endif

-include ../makefile.defs

# Add inputs and outputs from these tool invocations to the build variables 

# All Target
all: Nginx

# Tool invocations
Nginx: $(OBJS) $(USER_OBJS)
	@echo 'Building target: $@'
	@echo 'Invoking: GCC C Linker'
	gcc  -o"Nginx" $(OBJS) $(USER_OBJS) $(LIBS)
	@echo 'Finished building target: $@'
	@echo ' '

# Other Targets
clean:
	-$(RM) $(OBJS)$(C_DEPS)$(EXECUTABLES) Nginx
	-@echo ' '

.PHONY: all clean dependents
.SECONDARY:

-include ../makefile.targets
