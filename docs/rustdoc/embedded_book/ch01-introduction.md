# Introduction
Welcome to The Embedded Rust Book: An introductory book about using the Rust Programming Language on "Bare Metal" embedded systems, such as Microcontrollers.

Who Embedded Rust is For

Embedded Rust is for everyone who wants to do embedded programming while taking advantage of the higher-level concepts and safety guarantees the Rust language provides. (See also Who Rust Is For)

Scope

The goals of this book are:

Get developers up to speed with embedded Rust development. i.e. How to set up a development environment.

Share current best practices about using Rust for embedded development. i.e. How to best use Rust language features to write more correct embedded software.

Serve as a cookbook in some cases. e.g. How do I mix C and Rust in a single project?

This book tries to be as general as possible but to make things easier for both the readers and the writers it uses the ARM Cortex-M architecture in all its examples. However, the book doesn't assume that the reader is familiar with this particular architecture and explains details particular to this architecture where required.

Who This Book is For

This book caters towards people with either some embedded background or some Rust background, however we believe everybody curious about embedded Rust programming can get something out of this book. For those without any prior knowledge we suggest you read the "Assumptions and Prerequisites" section and catch up on missing knowledge to get more out of the book and improve your reading experience. You can check out the "Other Resources" section to find resources on topics you might want to catch up on.

Assumptions and Prerequisites

You are comfortable using the Rust Programming Language, and have written, run, and debugged Rust applications on a desktop environment. You should also be familiar with the idioms of the 2018 edition as this book targets Rust 2018.
You are comfortable developing and debugging embedded systems in another language such as C, C++, or Ada, and are familiar with concepts such as:
Cross Compilation
Memory Mapped Peripherals
Interrupts
Common interfaces such as I2C, SPI, Serial, etc.
Other Resources

If you are unfamiliar with anything mentioned above or if you want more information about a specific topic mentioned in this book you might find some of these resources helpful.

Topic	Resource	Description
Rust	Rust Book	If you are not yet comfortable with Rust, we highly suggest reading this book.
Rust, Embedded	Discovery Book	If you have never done any embedded programming, this book might be a better start
Rust, Embedded	Embedded Rust Bookshelf	Here you can find several other resources provided by Rust's Embedded Working Group.
Rust, Embedded	Embedonomicon	The nitty gritty details when doing embedded programming in Rust.
Rust, Embedded	embedded FAQ	Frequently asked questions about Rust in an embedded context.
Rust, Embedded	Comprehensive Rust 🦀: Bare Metal	Teaching material for a 1-day class on bare-metal Rust development
Interrupts	Interrupt	-
Memory-mapped IO/Peripherals	Memory-mapped I/O	-
SPI, UART, RS232, USB, I2C, TTL	Stack Exchange about SPI, UART, and other interfaces	-
Translations

This book has been translated by generous volunteers. If you would like your translation listed here, please open a PR to add it.

Japanese (repository)

Chinese (repository)

How to Use This Book

This book generally assumes that you’re reading it front-to-back. Later chapters build on concepts in earlier chapters, and earlier chapters may not dig into details on a topic, revisiting the topic in a later chapter.

This book will be using the STM32F3DISCOVERY development board from STMicroelectronics for the majority of the examples contained within. This board is based on the ARM Cortex-M architecture, and while basic functionality is the same across most CPUs based on this architecture, peripherals and other implementation details of Microcontrollers are different between different vendors, and often even different between Microcontroller families from the same vendor.

For this reason, we suggest purchasing the STM32F3DISCOVERY development board for the purpose of following the examples in this book.

Contributing to This Book

The work on this book is coordinated in this repository and is mainly developed by the resources team.

If you have trouble following the instructions in this book or find that some section of the book is not clear enough or hard to follow then that's a bug and it should be reported in the issue tracker of this book.

Pull requests fixing typos and adding new content are very welcome!

Re-using this material

This book is distributed under the following licenses:

The code samples and free-standing Cargo projects contained within this book are licensed under the terms of both the MIT License and the Apache License v2.0.
The written prose, pictures and diagrams contained within this book are licensed under the terms of the Creative Commons CC-BY-SA v4.0 license.
TL;DR: If you want to use our text or images in your work, you need to:

Give the appropriate credit (i.e. mention this book on your slide, and provide a link to the relevant page)
Provide a link to the CC-BY-SA v4.0 licence
Indicate if you have changed the material in any way, and make any changes to our material available under the same licence
Also, please do let us know if you find this book useful!

## Hardware

Let's get familiar with the hardware we'll be working with.

STM32F3DISCOVERY (the "F3")

F3

What does this board contain?

A STM32F303VCT6 microcontroller. This microcontroller has

A single-core ARM Cortex-M4F processor with hardware support for single-precision floating point operations and a maximum clock frequency of 72 MHz.

256 KiB of "Flash" memory. (1 KiB = 1024 bytes)

48 KiB of RAM.

A variety of integrated peripherals such as timers, I2C, SPI and USART.

General purpose Input Output (GPIO) and other types of pins accessible through the two rows of headers along side the board.

A USB interface accessible through the USB port labeled "USB USER".

An accelerometer as part of the LSM303DLHC chip.

A magnetometer as part of the LSM303DLHC chip.

A gyroscope as part of the L3GD20 chip.

8 user LEDs arranged in the shape of a compass.

A second microcontroller: a STM32F103. This microcontroller is actually part of an on-board programmer / debugger and is connected to the USB port named "USB ST-LINK".

For a more detailed list of features and further specifications of the board take a look at the STMicroelectronics website.

A word of caution: be careful if you want to apply external signals to the board. The microcontroller STM32F303VCT6 pins take a nominal voltage of 3.3 volts. For further information consult the 6.2 Absolute maximum ratings section in the manual

## no_std

The term Embedded Programming is used for a wide range of different classes of programming. Ranging from programming 8-Bit MCUs (like the ST72325xx) with just a few KB of RAM and ROM, up to systems like the Raspberry Pi (Model B 3+) which has a 32/64-bit 4-core Cortex-A53 @ 1.4 GHz and 1GB of RAM. Different restrictions/limitations will apply when writing code depending on what kind of target and use case you have.

There are two general Embedded Programming classifications:

Hosted Environments

These kinds of environments are close to a normal PC environment. What this means is that you are provided with a System Interface E.G. POSIX that provides you with primitives to interact with various systems, such as file systems, networking, memory management, threads, etc. Standard libraries in turn usually depend on these primitives to implement their functionality. You may also have some sort of sysroot and restrictions on RAM/ROM-usage, and perhaps some special HW or I/Os. Overall it feels like coding on a special-purpose PC environment.

Bare Metal Environments

In a bare metal environment no code has been loaded before your program. Without the software provided by an OS we can not load the standard library. Instead the program, along with the crates it uses, can only use the hardware (bare metal) to run. To prevent rust from loading the standard library use no_std. The platform-agnostic parts of the standard library are available through libcore. libcore also excludes things which are not always desirable in an embedded environment. One of these things is a memory allocator for dynamic memory allocation. If you require this or any other functionalities there are often crates which provide these.

The libstd Runtime

As mentioned before using libstd requires some sort of system integration, but this is not only because libstd is just providing a common way of accessing OS abstractions, it also provides a runtime. This runtime, among other things, takes care of setting up stack overflow protection, processing command line arguments, and spawning the main thread before a program's main function is invoked. This runtime also won't be available in a no_std environment.

Summary

#![no_std] is a crate-level attribute that indicates that the crate will link to the core-crate instead of the std-crate. The libcore crate in turn is a platform-agnostic subset of the std crate which makes no assumptions about the system the program will run on. As such, it provides APIs for language primitives like floats, strings and slices, as well as APIs that expose processor features like atomic operations and SIMD instructions. However it lacks APIs for anything that involves platform integration. Because of these properties no_std and libcore code can be used for any kind of bootstrapping (stage 0) code like bootloaders, firmware or kernels.

Overview

feature	no_std	std
heap (dynamic memory)	*	✓
collections (Vec, BTreeMap, etc)	**	✓
stack overflow protection	✘	✓
runs init code before main	✘	✓
libstd available	✘	✓
libcore available	✓	✓
writing firmware, kernel, or bootloader code	✓	✘
* Only if you use the alloc crate and use a suitable allocator like alloc-cortex-m.

** Only if you use the collections crate and configure a global default allocator.

** HashMap and HashSet are not available due to a lack of a secure random number generator.

See Also

RFC-1184
## Tooling

Dealing with microcontrollers involves using several different tools as we'll be dealing with an architecture different than your laptop's and we'll have to run and debug programs on a remote device.

We'll use all the tools listed below. Any recent version should work when a minimum version is not specified, but we have listed the versions we have tested.

Rust 1.31, 1.31-beta, or a newer toolchain PLUS ARM Cortex-M compilation support.
cargo-binutils ~0.1.4
qemu-system-arm. Tested versions: 3.0.0
OpenOCD >=0.8. Tested versions: v0.9.0 and v0.10.0
GDB with ARM support. Version 7.12 or newer highly recommended. Tested versions: 7.10, 7.11, 7.12 and 8.1
cargo-generate or git. These tools are optional but will make it easier to follow along with the book.
## Installation

cargo-generate OR git

Bare metal programs are non-standard (no_std) Rust programs that require some adjustments to the linking process in order to get the memory layout of the program right. This requires some additional files (like linker scripts) and settings (like linker flags). We have packaged those for you in a template such that you only need to fill in the missing information (such as the project name and the characteristics of your target hardware).

Our template is compatible with cargo-generate: a Cargo subcommand for creating new Cargo projects from templates. You can also download the template using git, curl, wget, or your web browser.

cargo-binutils

cargo-binutils is a collection of Cargo subcommands that make it easy to use the LLVM tools that are shipped with the Rust toolchain. These tools include the LLVM versions of objdump, nm and size and are used for inspecting binaries.

The advantage of using these tools over GNU binutils is that (a) installing the LLVM tools is the same one-command installation (rustup component add llvm-tools) regardless of your OS and (b) tools like objdump support all the architectures that rustc supports -- from ARM to x86_64 -- because they both share the same LLVM backend.

qemu-system-arm

QEMU is an emulator. In this case we use the variant that can fully emulate ARM systems. We use QEMU to run embedded programs on the host. Thanks to this you can follow some parts of this book even if you don't have any hardware with you!

Tooling for Embedded Rust Debugging

Overview

Debugging embedded systems in Rust requires specialized tools including software to manage the debugging process, debuggers to inspect and control program execution, and hardware probes to facilitate interaction between the host and the embedded device. This document outlines essential software tools like Probe-rs and OpenOCD, which simplify and support the debugging process, alongside prominent debuggers such as GDB and the Probe-rs Visual Studio Code extension. Additionally, it covers key hardware probes such as Rusty-probe, ST-Link, J-Link, and MCU-Link, which are integral for effective debugging and programming of embedded devices.

Software that drives debugging tools

Probe-rs

Probe-rs is a modern, Rust-focused software designed to work with debuggers in embedded systems. Unlike OpenOCD, Probe-rs is built with simplicity in mind and aims to reduce the configuration burden often found in other debugging solutions. It supports various probes and targets, providing a high-level interface for interacting with embedded hardware. Probe-rs integrates directly with Rust tooling, and integrates with Visual Studio Code through its extension, allowing developers to streamline their debugging workflow.

OpenOCD (Open On-Chip Debugger)

OpenOCD is an open-source software tool used for debugging, testing, and programming embedded systems. It provides an interface between the host system and embedded hardware, supporting various transport layers like JTAG and SWD (Serial Wire Debug). OpenOCD integrates with GDB, which is a debugger. OpenOCD is widely supported, with extensive documentation and a large community, but may require complex configuration, especially for custom embedded setups.

Debuggers

A debugger allows developers to inspect and control the execution of a program in order to identify and correct errors or bugs. It provides functionalities such as setting breakpoints, stepping through code line by line, and examining the values of variables and memory states. Debuggers are essential for thorough software development and maintenance, enabling developers to ensure that their code behaves as intended under various conditions.

Debuggers know how to:

Interact with the memory mapped registers.
Set Breakpoints/Watchpoints.
Read and write to the memory mapped registers.
Detect when the MCU has been halted for a debug event.
Continue MCU execution after a debug event has been encountered.
Erase and write to the microcontroller's FLASH.
Probe-rs Visual Studio Code Extension

Probe-rs has a Visual Studio Code extension, providing a seamless debugging experience without extensive setup. Through this connection, developers can use Rust-specific features like pretty printing and detailed error messages, ensuring that their debugging process aligns with the Rust ecosystem.

GDB (GNU Debugger)

GDB is a versatile debugging tool that allows developers to examine the state of programs while they run or after they crash. For embedded Rust, GDB connects to the target system via OpenOCD or other debugging servers to interact with the embedded code. GDB is highly configurable and supports features like remote debugging, variable inspection, and conditional breakpoints. It can be used on a variety of platforms, and has extensive support for Rust-specific debugging needs, such as pretty printing and integration with IDEs.

Probes

A hardware probe is a device used in the development and debugging of embedded systems to facilitate communication between a host computer and the target embedded device. It typically supports protocols like JTAG or SWD, enabling it to program, debug, and analyze the microcontroller or microprocessor on the embedded system. Hardware probes are crucial for developers to set breakpoints, step through code, and inspect memory and processor registers, effectively allowing them to diagnose and fix issues in real-time.

Rusty-probe

Rusty-probe is an open-sourced USB-based hardware debugging probe designed to work with probe-rs. The combination of Rusty-Probe and probe-rs provides an easy-to-use, cost-effective solution for developers working with embedded Rust applications.

ST-Link

The ST-Link is a popular debugging and programming probe developed by STMicroelectronics primarily for their STM32 and STM8 microcontroller series. It supports both debugging and programming via JTAG or SWD (Serial Wire Debug) interfaces. ST-Link is widely used due to its direct support from STMicroelectronics' extensive range of development boards and its integration into major IDEs, making it a convenient choice for developers working with STM microcontrollers.

J-Link

J-Link, developed by SEGGER Microcontroller, is a robust and versatile debugger supporting a wide range of CPU cores and devices beyond just ARM, such as RISC-V. Known for its high performance and reliability, J-Link supports various communication interfaces, including JTAG, SWD, and fine-pitch JTAG interfaces. It is favored for its advanced features like unlimited breakpoints in flash memory and its compatibility with a multitude of development environments.

MCU-Link

MCU-Link is a debugging probe that also functions as a programmer, provided by NXP Semiconductors. It supports a variety of ARM Cortex microcontrollers and interfaces seamlessly with development tools like MCUXpresso IDE. MCU-Link is particularly notable for its versatility and affordability, making it an accessible option for hobbyists, educators, and professional developers alike.

Installing the tools

This page contains OS-agnostic installation instructions for a few of the tools:

Rust Toolchain

Install rustup by following the instructions at https://rustup.rs.

NOTE Make sure you have a compiler version equal to or newer than 1.31. rustc -V should return a date newer than the one shown below.

$ rustc -V
rustc 1.31.1 (b6c32da9b 2018-12-18)
For bandwidth and disk usage concerns the default installation only supports native compilation. To add cross compilation support for the ARM Cortex-M architectures choose one of the following compilation targets. For the STM32F3DISCOVERY board used for the examples in this book, use the thumbv7em-none-eabihf target. Find the best Cortex-M for you.

Cortex-M0, M0+, and M1 (ARMv6-M architecture):

rustup target add thumbv6m-none-eabi
Cortex-M3 (ARMv7-M architecture):

rustup target add thumbv7m-none-eabi
Cortex-M4 and M7 without hardware floating point (ARMv7E-M architecture):

rustup target add thumbv7em-none-eabi
Cortex-M4F and M7F with hardware floating point (ARMv7E-M architecture):

rustup target add thumbv7em-none-eabihf
Cortex-M23 (ARMv8-M architecture):

rustup target add thumbv8m.base-none-eabi
Cortex-M33 and M35P (ARMv8-M architecture):

rustup target add thumbv8m.main-none-eabi
Cortex-M33F and M35PF with hardware floating point (ARMv8-M architecture):

rustup target add thumbv8m.main-none-eabihf
cargo-binutils

cargo install cargo-binutils

rustup component add llvm-tools
WINDOWS: prerequisite C++ Build Tools for Visual Studio 2019 is installed. https://visualstudio.microsoft.com/thank-you-downloading-visual-studio/?sku=BuildTools&rel=16

cargo-generate

We'll use this later to generate a project from a template.

cargo install cargo-generate
Note: on some Linux distros (e.g. Ubuntu) you may need to install the packages libssl-dev and pkg-config prior to installing cargo-generate.

OS-Specific Instructions

Now follow the instructions specific to the OS you are using:

### Linux
### Windows
### MacOS
Linux

Here are the installation commands for a few Linux distributions.

Packages

Ubuntu 18.04 or newer / Debian stretch or newer
NOTE gdb-multiarch is the GDB command you'll use to debug your ARM Cortex-M programs

sudo apt install gdb-multiarch openocd qemu-system-arm
Ubuntu 14.04 and 16.04
NOTE arm-none-eabi-gdb is the GDB command you'll use to debug your ARM Cortex-M programs

sudo apt install gdb-arm-none-eabi openocd qemu-system-arm
Fedora 27 or newer
sudo dnf install gdb openocd qemu-system-arm
Arch Linux
NOTE arm-none-eabi-gdb is the GDB command you'll use to debug ARM Cortex-M programs

sudo pacman -S arm-none-eabi-gdb qemu-system-arm openocd
udev rules

This rule lets you use OpenOCD with the Discovery board without root privilege.

Create the file /etc/udev/rules.d/70-st-link.rules with the contents shown below.

# STM32F3DISCOVERY rev A/B - ST-LINK/V2
ATTRS{idVendor}=="0483", ATTRS{idProduct}=="3748", TAG+="uaccess"

# STM32F3DISCOVERY rev C+ - ST-LINK/V2-1
ATTRS{idVendor}=="0483", ATTRS{idProduct}=="374b", TAG+="uaccess"
Then reload all the udev rules with:

sudo udevadm control --reload-rules
If you had the board plugged to your laptop, unplug it and then plug it again.

You can check the permissions by running this command:

lsusb
Which should show something like

(..)
Bus 001 Device 018: ID 0483:374b STMicroelectronics ST-LINK/V2.1
(..)
Take note of the bus and device numbers. Use those numbers to create a path like /dev/bus/usb/<bus>/<device>. Then use this path like so:

ls -l /dev/bus/usb/001/018
crw-------+ 1 root root 189, 17 Sep 13 12:34 /dev/bus/usb/001/018
getfacl /dev/bus/usb/001/018 | grep user
user::rw-
user:you:rw-
The + appended to permissions indicates the existence of an extended permission. The getfacl command tells the user you can make use of this device.

Now, go to the next section.

macOS

All the tools can be installed using Homebrew or MacPorts:

Install tools with Homebrew

$ # GDB
$ brew install arm-none-eabi-gdb

$ # OpenOCD
$ brew install openocd

$ # QEMU
$ brew install qemu
NOTE If OpenOCD crashes you may need to install the latest version using:

$ brew install --HEAD openocd
Install tools with MacPorts

$ # GDB
$ sudo port install arm-none-eabi-gcc

$ # OpenOCD
$ sudo port install openocd

$ # QEMU
$ sudo port install qemu
That's all! Go to the next section.

Windows

arm-none-eabi-gdb

ARM provides .exe installers for Windows. Grab one from here, and follow the instructions. Just before the installation process finishes tick/select the "Add path to environment variable" option. Then verify that the tools are in your %PATH%:

$ arm-none-eabi-gdb -v
GNU gdb (GNU Tools for Arm Embedded Processors 7-2018-q2-update) 8.1.0.20180315-git
(..)
OpenOCD

There's no official binary release of OpenOCD for Windows but if you're not in the mood to compile it yourself, the xPack project provides a binary distribution, here. Follow the provided installation instructions. Then update your %PATH% environment variable to include the path where the binaries were installed. (C:\Users\USERNAME\AppData\Roaming\xPacks\@xpack-dev-tools\openocd\0.10.0-13.1\.content\bin\, if you've been using the easy install)

Verify that OpenOCD is in your %PATH% with:

$ openocd -v
Open On-Chip Debugger 0.10.0
(..)
QEMU

Grab QEMU from the official website.

ST-LINK USB driver

You'll also need to install this USB driver or OpenOCD won't work. Follow the installer instructions and make sure you install the right version (32-bit or 64-bit) of the driver.

That's all! Go to the next section.

### Verify Installation

In this section we check that some of the required tools / drivers have been correctly installed and configured.

Connect your laptop / PC to the discovery board using a Mini-USB USB cable. The discovery board has two USB connectors; use the one labeled "USB ST-LINK" that sits on the center of the edge of the board.

Also check that the ST-LINK header is populated. See the picture below; the ST-LINK header is highlighted.

Connected discovery board

Now run the following command:

openocd -f interface/stlink.cfg -f target/stm32f3x.cfg
NOTE: Old versions of openocd, including the 0.10.0 release from 2017, do not contain the new (and preferable) interface/stlink.cfg file; instead you may need to use interface/stlink-v2.cfg or interface/stlink-v2-1.cfg.

You should get the following output and the program should block the console:

Open On-Chip Debugger 0.10.0
Licensed under GNU GPL v2
For bug reports, read
        http://openocd.org/doc/doxygen/bugs.html
Info : auto-selecting first available session transport "hla_swd". To override use 'transport select <transport>'.
adapter speed: 1000 kHz
adapter_nsrst_delay: 100
Info : The selected transport took over low-level target control. The results might differ compared to plain JTAG/SWD
none separate
Info : Unable to match requested speed 1000 kHz, using 950 kHz
Info : Unable to match requested speed 1000 kHz, using 950 kHz
Info : clock speed 950 kHz
Info : STLINK v2 JTAG v27 API v2 SWIM v15 VID 0x0483 PID 0x374B
Info : using stlink api v2
Info : Target voltage: 2.919881
Info : stm32f3x.cpu: hardware has 6 breakpoints, 4 watchpoints
The contents may not match exactly but you should get the last line about breakpoints and watchpoints. If you got it then terminate the OpenOCD process and move to the next section.

If you didn't get the "breakpoints" line then try one of the following commands.

openocd -f interface/stlink-v2.cfg -f target/stm32f3x.cfg
openocd -f interface/stlink-v2-1.cfg -f target/stm32f3x.cfg
If one of those commands works it means you got an old hardware revision of the discovery board. That won't be a problem but commit that fact to memory as you'll need to configure things a bit differently later on. You can move to the next section.

If none of the commands work as a normal user then try to run them with root permission (e.g. sudo openocd ..). If the commands do work with root permission then check that the udev rules have been correctly set.

If you have reached this point and OpenOCD is not working please open an issue and we'll help you out!
