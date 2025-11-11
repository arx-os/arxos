# Getting started
In this section we'll walk you through the process of writing, building, flashing and debugging embedded programs. You will be able to try most of the examples without any special hardware as we will show you the basics using QEMU, a popular open-source hardware emulator. The only section where hardware is required is, naturally enough, the Hardware section, where we use OpenOCD to program an STM32F3DISCOVERY.

## QEMU

We'll start writing a program for the LM3S6965, a Cortex-M3 microcontroller. We have chosen this as our initial target because it can be emulated using QEMU so you don't need to fiddle with hardware in this section and we can focus on the tooling and the development process.

IMPORTANT We'll use the name "app" for the project name in this tutorial. Whenever you see the word "app" you should replace it with the name you selected for your project. Or, you could also name your project "app" and avoid the substitutions.

Creating a non standard Rust program

We'll use the cortex-m-quickstart project template to generate a new project from it. The created project will contain a barebone application: a good starting point for a new embedded rust application. In addition, the project will contain an examples directory, with several separate applications, highlighting some of the key embedded rust functionality.

Using cargo-generate

First install cargo-generate

cargo install cargo-generate
Then generate a new project

cargo generate --git https://github.com/rust-embedded/cortex-m-quickstart
 Project Name: app
 Creating project called `app`...
 Done! New project created /tmp/app
cd app
Using git

Clone the repository

git clone https://github.com/rust-embedded/cortex-m-quickstart app
cd app
And then fill in the placeholders in the Cargo.toml file

[package]
authors = ["{{authors}}"] # "{{authors}}" -> "John Smith"
edition = "2018"
name = "{{project-name}}" # "{{project-name}}" -> "app"
version = "0.1.0"

# ..

[[bin]]
name = "{{project-name}}" # "{{project-name}}" -> "app"
test = false
bench = false
Using neither

Grab the latest snapshot of the cortex-m-quickstart template and extract it.

curl -LO https://github.com/rust-embedded/cortex-m-quickstart/archive/master.zip
unzip master.zip
mv cortex-m-quickstart-master app
cd app
Or you can browse to cortex-m-quickstart, click the green "Clone or download" button and then click "Download ZIP".

Then fill in the placeholders in the Cargo.toml file as done in the second part of the "Using git" version.

Program Overview

For convenience here are the most important parts of the source code in src/main.rs:

#![no_std]
#![no_main]

use panic_halt as _;

use cortex_m_rt::entry;

#[entry]
fn main() -> ! {
    loop {
        // your code goes here
    }
}
This program is a bit different from a standard Rust program so let's take a closer look.

#![no_std] indicates that this program will not link to the standard crate, std. Instead it will link to its subset: the core crate.

#![no_main] indicates that this program won't use the standard main interface that most Rust programs use. The main (no pun intended) reason to go with no_main is that using the main interface in no_std context requires nightly.

use panic_halt as _;. This crate provides a panic_handler that defines the panicking behavior of the program. We will cover this in more detail in the Panicking chapter of the book.

#[entry] is an attribute provided by the cortex-m-rt crate that's used to mark the entry point of the program. As we are not using the standard main interface we need another way to indicate the entry point of the program and that'd be #[entry].

fn main() -> !. Our program will be the only process running on the target hardware so we don't want it to end! We use a divergent function (the -> ! bit in the function signature) to ensure at compile time that'll be the case.

Cross compiling

The next step is to cross compile the program for the Cortex-M3 architecture. That's as simple as running cargo build --target $TRIPLE if you know what the compilation target ($TRIPLE) should be. Luckily, the .cargo/config.toml in the template has the answer:

tail -n6 .cargo/config.toml
[build]
# Pick ONE of these compilation targets
# target = "thumbv6m-none-eabi"    # Cortex-M0 and Cortex-M0+
target = "thumbv7m-none-eabi"    # Cortex-M3
# target = "thumbv7em-none-eabi"   # Cortex-M4 and Cortex-M7 (no FPU)
# target = "thumbv7em-none-eabihf" # Cortex-M4F and Cortex-M7F (with FPU)
To cross compile for the Cortex-M3 architecture we have to use thumbv7m-none-eabi. That target is not automatically installed when installing the Rust toolchain, it would now be a good time to add that target to the toolchain, if you haven't done it yet:

rustup target add thumbv7m-none-eabi
Since the thumbv7m-none-eabi compilation target has been set as the default in your .cargo/config.toml file, the two commands below do the same:

cargo build --target thumbv7m-none-eabi
cargo build
Inspecting

Now we have a non-native ELF binary in target/thumbv7m-none-eabi/debug/app. We can inspect it using cargo-binutils.

With cargo-readobj we can print the ELF headers to confirm that this is an ARM binary.

cargo readobj --bin app -- --file-headers
Note that:

--bin app is sugar for inspect the binary at target/$TRIPLE/debug/app
--bin app will also (re)compile the binary, if necessary
ELF Header:
  Magic:   7f 45 4c 46 01 01 01 00 00 00 00 00 00 00 00 00
  Class:                             ELF32
  Data:                              2's complement, little endian
  Version:                           1 (current)
  OS/ABI:                            UNIX - System V
  ABI Version:                       0x0
  Type:                              EXEC (Executable file)
  Machine:                           ARM
  Version:                           0x1
  Entry point address:               0x405
  Start of program headers:          52 (bytes into file)
  Start of section headers:          153204 (bytes into file)
  Flags:                             0x5000200
  Size of this header:               52 (bytes)
  Size of program headers:           32 (bytes)
  Number of program headers:         2
  Size of section headers:           40 (bytes)
  Number of section headers:         19
  Section header string table index: 18
cargo-size can print the size of the linker sections of the binary.

cargo size --bin app --release -- -A
we use --release to inspect the optimized version

app  :
section             size        addr
.vector_table       1024         0x0
.text                 92       0x400
.rodata                0       0x45c
.data                  0  0x20000000
.bss                   0  0x20000000
.debug_str          2958         0x0
.debug_loc            19         0x0
.debug_abbrev        567         0x0
.debug_info         4929         0x0
.debug_ranges         40         0x0
.debug_macinfo         1         0x0
.debug_pubnames     2035         0x0
.debug_pubtypes     1892         0x0
.ARM.attributes       46         0x0
.debug_frame         100         0x0
.debug_line          867         0x0
Total              14570
A refresher on ELF linker sections

.text contains the program instructions
.rodata contains constant values like strings
.data contains statically allocated variables whose initial values are not zero
.bss also contains statically allocated variables whose initial values are zero
.vector_table is a non-standard section that we use to store the vector (interrupt) table
.ARM.attributes and the .debug_* sections contain metadata and will not be loaded onto the target when flashing the binary.
IMPORTANT: ELF files contain metadata like debug information so their size on disk does not accurately reflect the space the program will occupy when flashed on a device. Always use cargo-size to check how big a binary really is.

cargo-objdump can be used to disassemble the binary.

cargo objdump --bin app --release -- --disassemble --no-show-raw-insn --print-imm-hex
NOTE if the above command complains about Unknown command line argument see the following bug report: https://github.com/rust-embedded/book/issues/269

NOTE this output can differ on your system. New versions of rustc, LLVM and libraries can generate different assembly. We truncated some of the instructions to keep the snippet small.

app:  file format ELF32-arm-little

Disassembly of section .text:
main:
     400: bl  #0x256
     404: b #-0x4 <main+0x4>

Reset:
     406: bl  #0x24e
     40a: movw  r0, #0x0
     < .. truncated any more instructions .. >

DefaultHandler_:
     656: b #-0x4 <DefaultHandler_>

UsageFault:
     657: strb  r7, [r4, #0x3]

DefaultPreInit:
     658: bx  lr

__pre_init:
     659: strb  r7, [r0, #0x1]

__nop:
     65a: bx  lr

HardFaultTrampoline:
     65c: mrs r0, msp
     660: b #-0x2 <HardFault_>

HardFault_:
     662: b #-0x4 <HardFault_>

HardFault:
     663: <unknown>
Running

Next, let's see how to run an embedded program on QEMU! This time we'll use the hello example which actually does something.

For convenience here's the source code of examples/hello.rs:

//! Prints "Hello, world!" on the host console using semihosting

#![no_main]
#![no_std]

use panic_halt as _;

use cortex_m_rt::entry;
use cortex_m_semihosting::{debug, hprintln};

#[entry]
fn main() -> ! {
    hprintln!("Hello, world!").unwrap();

    // exit QEMU
    // NOTE do not run this on hardware; it can corrupt OpenOCD state
    debug::exit(debug::EXIT_SUCCESS);

    loop {}
}
This program uses something called semihosting to print text to the host console. When using real hardware this requires a debug session but when using QEMU this Just Works.

Let's start by compiling the example:

cargo build --example hello
The output binary will be located at target/thumbv7m-none-eabi/debug/examples/hello.

To run this binary on QEMU run the following command:

qemu-system-arm \
  -cpu cortex-m3 \
  -machine lm3s6965evb \
  -nographic \
  -semihosting-config enable=on,target=native \
  -kernel target/thumbv7m-none-eabi/debug/examples/hello
Hello, world!
The command should successfully exit (exit code = 0) after printing the text. On *nix you can check that with the following command:

echo $?
0
Let's break down that QEMU command:

qemu-system-arm. This is the QEMU emulator. There are a few variants of these QEMU binaries; this one does full system emulation of ARM machines hence the name.

-cpu cortex-m3. This tells QEMU to emulate a Cortex-M3 CPU. Specifying the CPU model lets us catch some miscompilation errors: for example, running a program compiled for the Cortex-M4F, which has a hardware FPU, will make QEMU error during its execution.

-machine lm3s6965evb. This tells QEMU to emulate the LM3S6965EVB, an evaluation board that contains a LM3S6965 microcontroller.

-nographic. This tells QEMU to not launch its GUI.

-semihosting-config (..). This tells QEMU to enable semihosting. Semihosting lets the emulated device, among other things, use the host stdout, stderr and stdin and create files on the host.

-kernel $file. This tells QEMU which binary to load and run on the emulated machine.

Typing out that long QEMU command is too much work! We can set a custom runner to simplify the process. .cargo/config.toml has a commented out runner that invokes QEMU; let's uncomment it:

head -n3 .cargo/config.toml
[target.thumbv7m-none-eabi]
# uncomment this to make `cargo run` execute programs on QEMU
runner = "qemu-system-arm -cpu cortex-m3 -machine lm3s6965evb -nographic -semihosting-config enable=on,target=native -kernel"
This runner only applies to the thumbv7m-none-eabi target, which is our default compilation target. Now cargo run will compile the program and run it on QEMU:

cargo run --example hello --release
   Compiling app v0.1.0 (file:///tmp/app)
    Finished release [optimized + debuginfo] target(s) in 0.26s
     Running `qemu-system-arm -cpu cortex-m3 -machine lm3s6965evb -nographic -semihosting-config enable=on,target=native -kernel target/thumbv7m-none-eabi/release/examples/hello`
Hello, world!
Debugging

Debugging is critical to embedded development. Let's see how it's done.

Debugging an embedded device involves remote debugging as the program that we want to debug won't be running on the machine that's running the debugger program (GDB or LLDB).

Remote debugging involves a client and a server. In a QEMU setup, the client will be a GDB (or LLDB) process and the server will be the QEMU process that's also running the embedded program.

In this section we'll use the hello example we already compiled.

The first debugging step is to launch QEMU in debugging mode:

qemu-system-arm \
  -cpu cortex-m3 \
  -machine lm3s6965evb \
  -nographic \
  -semihosting-config enable=on,target=native \
  -gdb tcp::3333 \
  -S \
  -kernel target/thumbv7m-none-eabi/debug/examples/hello
This command won't print anything to the console and will block the terminal. We have passed two extra flags this time:

-gdb tcp::3333. This tells QEMU to wait for a GDB connection on TCP port 3333.

-S. This tells QEMU to freeze the machine at startup. Without this the program would have reached the end of main before we had a chance to launch the debugger!

Next we launch GDB in another terminal and tell it to load the debug symbols of the example:

gdb-multiarch -q target/thumbv7m-none-eabi/debug/examples/hello
NOTE: you might need another version of gdb instead of gdb-multiarch depending on which one you installed in the installation chapter. This could also be arm-none-eabi-gdb or just gdb.

Then within the GDB shell we connect to QEMU, which is waiting for a connection on TCP port 3333.

target remote :3333
Remote debugging using :3333
Reset () at $REGISTRY/cortex-m-rt-0.6.1/src/lib.rs:473
473     pub unsafe extern "C" fn Reset() -> ! {
You'll see that the process is halted and that the program counter is pointing to a function named Reset. That is the reset handler: what Cortex-M cores execute upon booting.

Note that on some setup, instead of displaying the line Reset () at $REGISTRY/cortex-m-rt-0.6.1/src/lib.rs:473 as shown above, gdb may print some warnings like :

core::num::bignum::Big32x40::mul_small () at src/libcore/num/bignum.rs:254 src/libcore/num/bignum.rs: No such file or directory.

That's a known glitch. You can safely ignore those warnings, you're most likely at Reset().

This reset handler will eventually call our main function. Let's skip all the way there using a breakpoint and the continue command. To set the breakpoint, let's first take a look where we would like to break in our code, with the list command.

list main
This will show the source code, from the file examples/hello.rs.

6       use panic_halt as _;
7
8       use cortex_m_rt::entry;
9       use cortex_m_semihosting::{debug, hprintln};
10
11      #[entry]
12      fn main() -> ! {
13          hprintln!("Hello, world!").unwrap();
14
15          // exit QEMU
We would like to add a breakpoint just before the "Hello, world!", which is on line 13. We do that with the break command:

break 13
We can now instruct gdb to run up to our main function, with the continue command:

continue
Continuing.

Breakpoint 1, hello::__cortex_m_rt_main () at examples\hello.rs:13
13          hprintln!("Hello, world!").unwrap();
We are now close to the code that prints "Hello, world!". Let's move forward using the next command.

next
16          debug::exit(debug::EXIT_SUCCESS);
At this point you should see "Hello, world!" printed on the terminal that's running qemu-system-arm.

$ qemu-system-arm (..)
Hello, world!
Calling next again will terminate the QEMU process.

next
[Inferior 1 (Remote target) exited normally]
You can now exit the GDB session.

quit
## Hardware

By now you should be somewhat familiar with the tooling and the development process. In this section we'll switch to real hardware; the process will remain largely the same. Let's dive in.

Know your hardware

Before we begin you need to identify some characteristics of the target device as these will be used to configure the project:

The ARM core. e.g. Cortex-M3.

Does the ARM core include an FPU? Cortex-M4F and Cortex-M7F cores do.

How much Flash memory and RAM does the target device have? e.g. 256 KiB of Flash and 32 KiB of RAM.

Where are Flash memory and RAM mapped in the address space? e.g. RAM is commonly located at address 0x2000_0000.

You can find this information in the data sheet or the reference manual of your device.

In this section we'll be using our reference hardware, the STM32F3DISCOVERY. This board contains an STM32F303VCT6 microcontroller. This microcontroller has:

A Cortex-M4F core that includes a single precision FPU

256 KiB of Flash located at address 0x0800_0000.

40 KiB of RAM located at address 0x2000_0000. (There's another RAM region but for simplicity we'll ignore it).

Configuring

We'll start from scratch with a fresh template instance. Refer to the previous section on QEMU for a refresher on how to do this without cargo-generate.

$ cargo generate --git https://github.com/rust-embedded/cortex-m-quickstart
 Project Name: app
 Creating project called `app`...
 Done! New project created /tmp/app

$ cd app
Step number one is to set a default compilation target in .cargo/config.toml.

tail -n5 .cargo/config.toml
# Pick ONE of these compilation targets
# target = "thumbv6m-none-eabi"    # Cortex-M0 and Cortex-M0+
# target = "thumbv7m-none-eabi"    # Cortex-M3
# target = "thumbv7em-none-eabi"   # Cortex-M4 and Cortex-M7 (no FPU)
target = "thumbv7em-none-eabihf" # Cortex-M4F and Cortex-M7F (with FPU)
We'll use thumbv7em-none-eabihf as that covers the Cortex-M4F core.

NOTE: As you may remember from the previous chapter, we have to install all targets and this is a new one. So don't forget to run the installation process rustup target add thumbv7em-none-eabihf for this target.

The second step is to enter the memory region information into the memory.x file.

$ cat memory.x
/* Linker script for the STM32F303VCT6 */
MEMORY
{
  /* NOTE 1 K = 1 KiBi = 1024 bytes */
  FLASH : ORIGIN = 0x08000000, LENGTH = 256K
  RAM : ORIGIN = 0x20000000, LENGTH = 40K
}
NOTE: If you for some reason changed the memory.x file after you had made the first build of a specific build target, then do cargo clean before cargo build, because cargo build may not track updates of memory.x.

We'll start with the hello example again, but first we have to make a small change.

In examples/hello.rs, make sure the debug::exit() call is commented out or removed. It is used only for running in QEMU.

#[entry]
fn main() -> ! {
    hprintln!("Hello, world!").unwrap();

    // exit QEMU
    // NOTE do not run this on hardware; it can corrupt OpenOCD state
    // debug::exit(debug::EXIT_SUCCESS);

    loop {}
}
You can now cross compile programs using cargo build and inspect the binaries using cargo-binutils as you did before. The cortex-m-rt crate handles all the magic required to get your chip running, as helpfully, pretty much all Cortex-M CPUs boot in the same fashion.

cargo build --example hello
Debugging

Debugging will look a bit different. In fact, the first steps can look different depending on the target device. In this section we'll show the steps required to debug a program running on the STM32F3DISCOVERY. This is meant to serve as a reference; for device specific information about debugging check out the Debugonomicon.

As before we'll do remote debugging and the client will be a GDB process. This time, however, the server will be OpenOCD.

As done during the verify section connect the discovery board to your laptop / PC and check that the ST-LINK header is populated.

On a terminal run openocd to connect to the ST-LINK on the discovery board. Run this command from the root of the template; openocd will pick up the openocd.cfg file which indicates which interface file and target file to use.

cat openocd.cfg
# Sample OpenOCD configuration for the STM32F3DISCOVERY development board

# Depending on the hardware revision you got you'll have to pick ONE of these
# interfaces. At any time only one interface should be commented out.

# Revision C (newer revision)
source [find interface/stlink.cfg]

# Revision A and B (older revisions)
# source [find interface/stlink-v2.cfg]

source [find target/stm32f3x.cfg]
NOTE If you found out that you have an older revision of the discovery board during the verify section then you should modify the openocd.cfg file at this point to use interface/stlink-v2.cfg.

$ openocd
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
Info : Target voltage: 2.913879
Info : stm32f3x.cpu: hardware has 6 breakpoints, 4 watchpoints
On another terminal run GDB, also from the root of the template.

gdb-multiarch -q target/thumbv7em-none-eabihf/debug/examples/hello
NOTE: like before you might need another version of gdb instead of gdb-multiarch depending on which one you installed in the installation chapter. This could also be arm-none-eabi-gdb or just gdb.

Next connect GDB to OpenOCD, which is waiting for a TCP connection on port 3333.

(gdb) target remote :3333
Remote debugging using :3333
0x00000000 in ?? ()
Now proceed to flash (load) the program onto the microcontroller using the load command.

(gdb) load
Loading section .vector_table, size 0x400 lma 0x8000000
Loading section .text, size 0x1518 lma 0x8000400
Loading section .rodata, size 0x414 lma 0x8001918
Start address 0x08000400, load size 7468
Transfer rate: 13 KB/sec, 2489 bytes/write.
The program is now loaded. This program uses semihosting so before we do any semihosting call we have to tell OpenOCD to enable semihosting. You can send commands to OpenOCD using the monitor command.

(gdb) monitor arm semihosting enable
semihosting is enabled
You can see all the OpenOCD commands by invoking the monitor help command.

Like before we can skip all the way to main using a breakpoint and the continue command.

(gdb) break main
Breakpoint 1 at 0x8000490: file examples/hello.rs, line 11.
Note: automatically using hardware breakpoints for read-only addresses.

(gdb) continue
Continuing.

Breakpoint 1, hello::__cortex_m_rt_main_trampoline () at examples/hello.rs:11
11      #[entry]
NOTE If GDB blocks the terminal instead of hitting the breakpoint after you issue the continue command above, you might want to double check that the memory region information in the memory.x file is correctly set up for your device (both the starts and lengths).

Step into the main function with step.

(gdb) step
halted: PC: 0x08000496
hello::__cortex_m_rt_main () at examples/hello.rs:13
13          hprintln!("Hello, world!").unwrap();
After advancing the program with next you should see "Hello, world!" printed on the OpenOCD console, among other stuff.

$ openocd
(..)
Info : halted: PC: 0x08000502
Hello, world!
Info : halted: PC: 0x080004ac
Info : halted: PC: 0x080004ae
Info : halted: PC: 0x080004b0
Info : halted: PC: 0x080004b4
Info : halted: PC: 0x080004b8
Info : halted: PC: 0x080004bc
The message is only displayed once as the program is about to enter the infinite loop defined in line 19: loop {}

You can now exit GDB using the quit command.

(gdb) quit
A debugging session is active.

        Inferior 1 [Remote target] will be detached.

Quit anyway? (y or n)
Debugging now requires a few more steps so we have packed all those steps into a single GDB script named openocd.gdb. The file was created during the cargo generate step, and should work without any modifications. Let's have a peek:

cat openocd.gdb
target extended-remote :3333

# print demangled symbols
set print asm-demangle on

# detect unhandled exceptions, hard faults and panics
break DefaultHandler
break HardFault
break rust_begin_unwind

monitor arm semihosting enable

load

# start the process but immediately halt the processor
stepi
Now running <gdb> -x openocd.gdb target/thumbv7em-none-eabihf/debug/examples/hello will immediately connect GDB to OpenOCD, enable semihosting, load the program and start the process.

Alternatively, you can turn <gdb> -x openocd.gdb into a custom runner to make cargo run build a program and start a GDB session. This runner is included in .cargo/config.toml but it's commented out.

head -n10 .cargo/config.toml
[target.thumbv7m-none-eabi]
# uncomment this to make `cargo run` execute programs on QEMU
# runner = "qemu-system-arm -cpu cortex-m3 -machine lm3s6965evb -nographic -semihosting-config enable=on,target=native -kernel"

[target.'cfg(all(target_arch = "arm", target_os = "none"))']
# uncomment ONE of these three option to make `cargo run` start a GDB session
# which option to pick depends on your system
runner = "arm-none-eabi-gdb -x openocd.gdb"
# runner = "gdb-multiarch -x openocd.gdb"
# runner = "gdb -x openocd.gdb"
$ cargo run --example hello
(..)
Loading section .vector_table, size 0x400 lma 0x8000000
Loading section .text, size 0x1e70 lma 0x8000400
Loading section .rodata, size 0x61c lma 0x8002270
Start address 0x800144e, load size 10380
Transfer rate: 17 KB/sec, 3460 bytes/write.
(gdb)
## Memory-mapped Registers

Embedded systems can only get so far by executing normal Rust code and moving data around in RAM. If we want to get any information into or out of our system (be that blinking an LED, detecting a button press or communicating with an off-chip peripheral on some sort of bus) we're going to have to dip into the world of Peripherals and their 'memory mapped registers'.

You may well find that the code you need to access the peripherals in your micro-controller has already been written, at one of the following levels:

Common crates

Micro-architecture Crate - This sort of crate handles any useful routines common to the processor core your microcontroller is using, as well as any peripherals that are common to all micro-controllers that use that particular type of processor core. For example the cortex-m crate gives you functions to enable and disable interrupts, which are the same for all Cortex-M based micro-controllers. It also gives you access to the 'SysTick' peripheral included with all Cortex-M based micro-controllers.
Peripheral Access Crate (PAC) - This sort of crate is a thin wrapper over the various memory-wrapper registers defined for your particular part-number of micro-controller you are using. For example, tm4c123x for the Texas Instruments Tiva-C TM4C123 series, or stm32f30x for the ST-Micro STM32F30x series. Here, you'll be interacting with the registers directly, following each peripheral's operating instructions given in your micro-controller's Technical Reference Manual.
HAL Crate - These crates offer a more user-friendly API for your particular processor, often by implementing some common traits defined in embedded-hal. For example, this crate might offer a Serial struct, with a constructor that takes an appropriate set of GPIO pins and a baud rate, and offers some sort of write_byte function for sending data. See the chapter on Portability for more information on embedded-hal.
Board Crate - These crates go one step further than a HAL Crate by pre-configuring various peripherals and GPIO pins to suit the specific developer kit or board you are using, such as stm32f3-discovery for the STM32F3DISCOVERY board.
Board Crate

A board crate is the perfect starting point, if you're new to embedded Rust. They nicely abstract the HW details that might be overwhelming when starting studying this subject, and makes standard tasks easy, like turning a LED on or off. The functionality it exposes varies a lot between boards. Since this book aims at staying hardware agnostic, the board crates won't be covered by this book.

If you want to experiment with the STM32F3DISCOVERY board, it is highly recommended to take a look at the stm32f3-discovery board crate, which provides functionality to blink the board LEDs, access its compass, bluetooth and more. The Discovery book offers a great introduction to the use of a board crate.

But if you're working on a system that doesn't yet have dedicated board crate, or you need functionality not provided by existing crates, read on as we start from the bottom, with the micro-architecture crates.

Micro-architecture crate

Let's look at the SysTick peripheral that's common to all Cortex-M based micro-controllers. We can find a pretty low-level API in the cortex-m crate, and we can use it like this:

#![no_std]
#![no_main]
use cortex_m::peripheral::{syst, Peripherals};
use cortex_m_rt::entry;
use panic_halt as _;

#[entry]
fn main() -> ! {
    let peripherals = Peripherals::take().unwrap();
    let mut systick = peripherals.SYST;
    systick.set_clock_source(syst::SystClkSource::Core);
    systick.set_reload(1_000);
    systick.clear_current();
    systick.enable_counter();
    while !systick.has_wrapped() {
        // Loop
    }

    loop {}
}
The functions on the SYST struct map pretty closely to the functionality defined by the ARM Technical Reference Manual for this peripheral. There's nothing in this API about 'delaying for X milliseconds' - we have to crudely implement that ourselves using a while loop. Note that we can't access our SYST struct until we have called Peripherals::take() - this is a special routine that guarantees that there is only one SYST structure in our entire program. For more on that, see the Peripherals section.

Using a Peripheral Access Crate (PAC)

We won't get very far with our embedded software development if we restrict ourselves to only the basic peripherals included with every Cortex-M. At some point, we're going to need to write some code that's specific to the particular micro-controller we're using. In this example, let's assume we have an Texas Instruments TM4C123 - a middling 80MHz Cortex-M4 with 256 KiB of Flash. We're going to pull in the tm4c123x crate to make use of this chip.

#![no_std]
#![no_main]

use panic_halt as _; // panic handler

use cortex_m_rt::entry;
use tm4c123x;

#[entry]
pub fn init() -> (Delay, Leds) {
    let cp = cortex_m::Peripherals::take().unwrap();
    let p = tm4c123x::Peripherals::take().unwrap();

    let pwm = p.PWM0;
    pwm.ctl.write(|w| w.globalsync0().clear_bit());
    // Mode = 1 => Count up/down mode
    pwm._2_ctl.write(|w| w.enable().set_bit().mode().set_bit());
    pwm._2_gena.write(|w| w.actcmpau().zero().actcmpad().one());
    // 528 cycles (264 up and down) = 4 loops per video line (2112 cycles)
    pwm._2_load.write(|w| unsafe { w.load().bits(263) });
    pwm._2_cmpa.write(|w| unsafe { w.compa().bits(64) });
    pwm.enable.write(|w| w.pwm4en().set_bit());
}
We've accessed the PWM0 peripheral in exactly the same way as we accessed the SYST peripheral earlier, except we called tm4c123x::Peripherals::take(). As this crate was auto-generated using svd2rust, the access functions for our register fields take a closure, rather than a numeric argument. While this looks like a lot of code, the Rust compiler can use it to perform a bunch of checks for us, but then generate machine-code which is pretty close to hand-written assembler! Where the auto-generated code isn't able to determine that all possible arguments to a particular accessor function are valid (for example, if the SVD defines the register as 32-bit but doesn't say if some of those 32-bit values have a special meaning), then the function is marked as unsafe. We can see this in the example above when setting the load and compa sub-fields using the bits() function.

Reading

The read() function returns an object which gives read-only access to the various sub-fields within this register, as defined by the manufacturer's SVD file for this chip. You can find all the functions available on special R return type for this particular register, in this particular peripheral, on this particular chip, in the tm4c123x documentation.

if pwm.ctl.read().globalsync0().is_set() {
    // Do a thing
}
Writing

The write() function takes a closure with a single argument. Typically we call this w. This argument then gives read-write access to the various sub-fields within this register, as defined by the manufacturer's SVD file for this chip. Again, you can find all the functions available on the 'w' for this particular register, in this particular peripheral, on this particular chip, in the tm4c123x documentation. Note that all of the sub-fields that we do not set will be set to a default value for us - any existing content in the register will be lost.

pwm.ctl.write(|w| w.globalsync0().clear_bit());
Modifying

If we wish to change only one particular sub-field in this register and leave the other sub-fields unchanged, we can use the modify function. This function takes a closure with two arguments - one for reading and one for writing. Typically we call these r and w respectively. The r argument can be used to inspect the current contents of the register, and the w argument can be used to modify the register contents.

pwm.ctl.modify(|r, w| w.globalsync0().clear_bit());
The modify function really shows the power of closures here. In C, we'd have to read into some temporary value, modify the correct bits and then write the value back. This means there's considerable scope for error:

uint32_t temp = pwm0.ctl.read();
temp |= PWM0_CTL_GLOBALSYNC0;
pwm0.ctl.write(temp);
uint32_t temp2 = pwm0.enable.read();
temp2 |= PWM0_ENABLE_PWM4EN;
pwm0.enable.write(temp); // Uh oh! Wrong variable!
Using a HAL crate

The HAL crate for a chip typically works by implementing a custom Trait for the raw structures exposed by the PAC. Often this trait will define a function called constrain() for single peripherals or split() for things like GPIO ports with multiple pins. This function will consume the underlying raw peripheral structure and return a new object with a higher-level API. This API may also do things like have the Serial port new function require a borrow on some Clock structure, which can only be generated by calling the function which configures the PLLs and sets up all the clock frequencies. In this way, it is statically impossible to create a Serial port object without first having configured the clock rates, or for the Serial port object to misconvert the baud rate into clock ticks. Some crates even define special traits for the states each GPIO pin can be in, requiring the user to put a pin into the correct state (say, by selecting the appropriate Alternate Function Mode) before passing the pin into Peripheral. All with no run-time cost!

Let's see an example:

#![no_std]
#![no_main]

use panic_halt as _; // panic handler

use cortex_m_rt::entry;
use tm4c123x_hal as hal;
use tm4c123x_hal::prelude::*;
use tm4c123x_hal::serial::{NewlineMode, Serial};
use tm4c123x_hal::sysctl;

#[entry]
fn main() -> ! {
    let p = hal::Peripherals::take().unwrap();
    let cp = hal::CorePeripherals::take().unwrap();

    // Wrap up the SYSCTL struct into an object with a higher-layer API
    let mut sc = p.SYSCTL.constrain();
    // Pick our oscillation settings
    sc.clock_setup.oscillator = sysctl::Oscillator::Main(
        sysctl::CrystalFrequency::_16mhz,
        sysctl::SystemClock::UsePll(sysctl::PllOutputFrequency::_80_00mhz),
    );
    // Configure the PLL with those settings
    let clocks = sc.clock_setup.freeze();

    // Wrap up the GPIO_PORTA struct into an object with a higher-layer API.
    // Note it needs to borrow `sc.power_control` so it can power up the GPIO
    // peripheral automatically.
    let mut porta = p.GPIO_PORTA.split(&sc.power_control);

    // Activate the UART.
    let uart = Serial::uart0(
        p.UART0,
        // The transmit pin
        porta
            .pa1
            .into_af_push_pull::<hal::gpio::AF1>(&mut porta.control),
        // The receive pin
        porta
            .pa0
            .into_af_push_pull::<hal::gpio::AF1>(&mut porta.control),
        // No RTS or CTS required
        (),
        (),
        // The baud rate
        115200_u32.bps(),
        // Output handling
        NewlineMode::SwapLFtoCRLF,
        // We need the clock rates to calculate the baud rate divisors
        &clocks,
        // We need this to power up the UART peripheral
        &sc.power_control,
    );

    loop {
        writeln!(uart, "Hello, World!\r\n").unwrap();
    }
}
## Semihosting

Semihosting is a mechanism that lets embedded devices do I/O on the host and is mainly used to log messages to the host console. Semihosting requires a debug session and pretty much nothing else (no extra wires!) so it's super convenient to use. The downside is that it's super slow: each write operation can take several milliseconds depending on the hardware debugger (e.g. ST-Link) you use.

The cortex-m-semihosting crate provides an API to do semihosting operations on Cortex-M devices. The program below is the semihosting version of "Hello, world!":

#![no_main]
#![no_std]

use panic_halt as _;

use cortex_m_rt::entry;
use cortex_m_semihosting::hprintln;

#[entry]
fn main() -> ! {
    hprintln!("Hello, world!").unwrap();

    loop {}
}
If you run this program on hardware you'll see the "Hello, world!" message within the OpenOCD logs.

$ openocd
(..)
Hello, world!
(..)
You do need to enable semihosting in OpenOCD from GDB first:

(gdb) monitor arm semihosting enable
semihosting is enabled
QEMU understands semihosting operations so the above program will also work with qemu-system-arm without having to start a debug session. Note that you'll need to pass the -semihosting-config flag to QEMU to enable semihosting support; these flags are already included in the .cargo/config.toml file of the template.

$ # this program will block the terminal
$ cargo run
     Running `qemu-system-arm (..)
Hello, world!
There's also an exit semihosting operation that can be used to terminate the QEMU process. Important: do not use debug::exit on hardware; this function can corrupt your OpenOCD session and you will not be able to debug more programs until you restart it.

#![no_main]
#![no_std]

use panic_halt as _;

use cortex_m_rt::entry;
use cortex_m_semihosting::debug;

#[entry]
fn main() -> ! {
    let roses = "blue";

    if roses == "red" {
        debug::exit(debug::EXIT_SUCCESS);
    } else {
        debug::exit(debug::EXIT_FAILURE);
    }

    loop {}
}
$ cargo run
     Running `qemu-system-arm (..)

$ echo $?
1
One last tip: you can set the panicking behavior to exit(EXIT_FAILURE). This will let you write no_std run-pass tests that you can run on QEMU.

For convenience, the panic-semihosting crate has an "exit" feature that when enabled invokes exit(EXIT_FAILURE) after logging the panic message to the host stderr.

#![no_main]
#![no_std]

use panic_semihosting as _; // features = ["exit"]

use cortex_m_rt::entry;
use cortex_m_semihosting::debug;

#[entry]
fn main() -> ! {
    let roses = "blue";

    assert_eq!(roses, "red");

    loop {}
}
$ cargo run
     Running `qemu-system-arm (..)
panicked at 'assertion failed: `(left == right)`
  left: `"blue"`,
 right: `"red"`', examples/hello.rs:15:5

$ echo $?
1
NOTE: To enable this feature on panic-semihosting, edit your Cargo.toml dependencies section where panic-semihosting is specified with:

panic-semihosting = { version = "VERSION", features = ["exit"] }
where VERSION is the version desired. For more information on dependencies features check the specifying dependencies section of the Cargo book.

## Panicking

Panicking is a core part of the Rust language. Built-in operations like indexing are runtime checked for memory safety. When out of bounds indexing is attempted this results in a panic.

In the standard library panicking has a defined behavior: it unwinds the stack of the panicking thread, unless the user opted for aborting the program on panics.

In programs without standard library, however, the panicking behavior is left undefined. A behavior can be chosen by declaring a #[panic_handler] function. This function must appear exactly once in the dependency graph of a program, and must have the following signature: fn(&PanicInfo) -> !, where PanicInfo is a struct containing information about the location of the panic.

Given that embedded systems range from user facing to safety critical (cannot crash) there's no one size fits all panicking behavior but there are plenty of commonly used behaviors. These common behaviors have been packaged into crates that define the #[panic_handler] function. Some examples include:

panic-abort. A panic causes the abort instruction to be executed.
panic-halt. A panic causes the program, or the current thread, to halt by entering an infinite loop.
panic-itm. The panicking message is logged using the ITM, an ARM Cortex-M specific peripheral.
panic-semihosting. The panicking message is logged to the host using the semihosting technique.
You may be able to find even more crates searching for the panic-handler keyword on crates.io.

A program can pick one of these behaviors simply by linking to the corresponding crate. The fact that the panicking behavior is expressed in the source of an application as a single line of code is not only useful as documentation but can also be used to change the panicking behavior according to the compilation profile. For example:

#![no_main]
#![no_std]

// dev profile: easier to debug panics; can put a breakpoint on `rust_begin_unwind`
#[cfg(debug_assertions)]
use panic_halt as _;

// release profile: minimize the binary size of the application
#[cfg(not(debug_assertions))]
use panic_abort as _;

// ..
In this example the crate links to the panic-halt crate when built with the dev profile (cargo build), but links to the panic-abort crate when built with the release profile (cargo build --release).

The use panic_abort as _; form of the use statement is used to ensure the panic_abort panic handler is included in our final executable while making it clear to the compiler that we won't explicitly use anything from the crate. Without the as _ rename, the compiler would warn that we have an unused import. Sometimes you might see extern crate panic_abort instead, which is an older style used before the 2018 edition of Rust, and should now only be used for "sysroot" crates (those distributed with Rust itself) such as proc_macro, alloc, std, and test.

An example

Here's an example that tries to index an array beyond its length. The operation results in a panic.

#![no_main]
#![no_std]

use panic_semihosting as _;

use cortex_m_rt::entry;

#[entry]
fn main() -> ! {
    let xs = [0, 1, 2];
    let i = xs.len();
    let _y = xs[i]; // out of bounds access

    loop {}
}
This example chose the panic-semihosting behavior which prints the panic message to the host console using semihosting.

$ cargo run
     Running `qemu-system-arm -cpu cortex-m3 -machine lm3s6965evb (..)
panicked at 'index out of bounds: the len is 3 but the index is 4', src/main.rs:12:13
You can try changing the behavior to panic-halt and confirm that no message is printed in that case.

## Exceptions

Exceptions, and interrupts, are a hardware mechanism by which the processor handles asynchronous events and fatal errors (e.g. executing an invalid instruction). Exceptions imply preemption and involve exception handlers, subroutines executed in response to the signal that triggered the event.

The cortex-m-rt crate provides an exception attribute to declare exception handlers.

// Exception handler for the SysTick (System Timer) exception
#[exception]
fn SysTick() {
    // ..
}
Other than the exception attribute exception handlers look like plain functions but there's one more difference: exception handlers can not be called by software. Following the previous example, the statement SysTick(); would result in a compilation error.

This behavior is pretty much intended and it's required to provide a feature: static mut variables declared inside exception handlers are safe to use.

#[exception]
fn SysTick() {
    static mut COUNT: u32 = 0;

    // `COUNT` has transformed to type `&mut u32` and it's safe to use
    *COUNT += 1;
}
As you may know, using static mut variables in a function makes it non-reentrant. It's undefined behavior to call a non-reentrant function, directly or indirectly, from more than one exception / interrupt handler or from main and one or more exception / interrupt handlers.

Safe Rust must never result in undefined behavior so non-reentrant functions must be marked as unsafe. Yet I just told that exception handlers can safely use static mut variables. How is this possible? This is possible because exception handlers can not be called by software thus reentrancy is not possible. These handlers are called by the hardware itself which is assumed to be physically non-concurrent.

As a result, in the context of exception handlers in embedded systems, the absence of concurrent invocations of the same handler ensures that there are no reentrancy issues, even if the handler uses static mutable variables.

In a multicore system, where multiple processor cores are executing code concurrently, the potential for reentrancy issues becomes relevant again, even within exception handlers. While each core may have its own set of exception handlers, there can still be scenarios where multiple cores attempt to execute the same exception handler simultaneously.
To address this concern in a multicore environment, proper synchronization mechanisms need to be employed within the exception handlers to ensure that access to shared resources is properly coordinated among the cores. This typically involves the use of techniques such as locks, semaphores, or atomic operations to prevent data races and maintain data integrity

Note that the exception attribute transforms definitions of static variables inside the function by wrapping them into unsafe blocks and providing us with new appropriate variables of type &mut of the same name. Thus we can dereference the reference via * to access the values of the variables without needing to wrap them in an unsafe block.

A complete example

Here's an example that uses the system timer to raise a SysTick exception roughly every second. The SysTick exception handler keeps track of how many times it has been called in the COUNT variable and then prints the value of COUNT to the host console using semihosting.

NOTE: You can run this example on any Cortex-M device; you can also run it on QEMU

#![deny(unsafe_code)]
#![no_main]
#![no_std]

use panic_halt as _;

use core::fmt::Write;

use cortex_m::peripheral::syst::SystClkSource;
use cortex_m_rt::{entry, exception};
use cortex_m_semihosting::{
    debug,
    hio::{self, HostStream},
};

#[entry]
fn main() -> ! {
    let p = cortex_m::Peripherals::take().unwrap();
    let mut syst = p.SYST;

    // configures the system timer to trigger a SysTick exception every second
    syst.set_clock_source(SystClkSource::Core);
    // this is configured for the LM3S6965 which has a default CPU clock of 12 MHz
    syst.set_reload(12_000_000);
    syst.clear_current();
    syst.enable_counter();
    syst.enable_interrupt();

    loop {}
}

#[exception]
fn SysTick() {
    static mut COUNT: u32 = 0;
    static mut STDOUT: Option<HostStream> = None;

    *COUNT += 1;

    // Lazy initialization
    if STDOUT.is_none() {
        *STDOUT = hio::hstdout().ok();
    }

    if let Some(hstdout) = STDOUT.as_mut() {
        write!(hstdout, "{}", *COUNT).ok();
    }

    // IMPORTANT omit this `if` block if running on real hardware or your
    // debugger will end in an inconsistent state
    if *COUNT == 9 {
        // This will terminate the QEMU process
        debug::exit(debug::EXIT_SUCCESS);
    }
}
tail -n5 Cargo.toml
[dependencies]
cortex-m = "0.5.7"
cortex-m-rt = "0.6.3"
panic-halt = "0.2.0"
cortex-m-semihosting = "0.3.1"
$ cargo run --release
     Running `qemu-system-arm -cpu cortex-m3 -machine lm3s6965evb (..)
123456789
If you run this on the Discovery board you'll see the output on the OpenOCD console. Also, the program will not stop when the count reaches 9.

The default exception handler

What the exception attribute actually does is override the default exception handler for a specific exception. If you don't override the handler for a particular exception it will be handled by the DefaultHandler function, which defaults to:

fn DefaultHandler() {
    loop {}
}
This function is provided by the cortex-m-rt crate and marked as #[no_mangle] so you can put a breakpoint on "DefaultHandler" and catch unhandled exceptions.

It's possible to override this DefaultHandler using the exception attribute:

#[exception]
fn DefaultHandler(irqn: i16) {
    // custom default handler
}
The irqn argument indicates which exception is being serviced. A negative value indicates that a Cortex-M exception is being serviced; and zero or a positive value indicate that a device specific exception, AKA interrupt, is being serviced.

The hard fault handler

The HardFault exception is a bit special. This exception is fired when the program enters an invalid state so its handler can not return as that could result in undefined behavior. Also, the runtime crate does a bit of work before the user defined HardFault handler is invoked to improve debuggability.

The result is that the HardFault handler must have the following signature: fn(&ExceptionFrame) -> !. The argument of the handler is a pointer to registers that were pushed into the stack by the exception. These registers are a snapshot of the processor state at the moment the exception was triggered and are useful to diagnose a hard fault.

Here's an example that performs an illegal operation: a read to a nonexistent memory location.

NOTE: This program won't work, i.e. it won't crash, on QEMU because qemu-system-arm -machine lm3s6965evb doesn't check memory loads and will happily return 0 on reads to invalid memory.

#![no_main]
#![no_std]

use panic_halt as _;

use core::fmt::Write;
use core::ptr;

use cortex_m_rt::{entry, exception, ExceptionFrame};
use cortex_m_semihosting::hio;

#[entry]
fn main() -> ! {
    // read a nonexistent memory location
    unsafe {
        ptr::read_volatile(0x3FFF_0000 as *const u32);
    }

    loop {}
}

#[exception]
fn HardFault(ef: &ExceptionFrame) -> ! {
    if let Ok(mut hstdout) = hio::hstdout() {
        writeln!(hstdout, "{:#?}", ef).ok();
    }

    loop {}
}
The HardFault handler prints the ExceptionFrame value. If you run this you'll see something like this on the OpenOCD console.

$ openocd
(..)
ExceptionFrame {
    r0: 0x3fff0000,
    r1: 0x00000003,
    r2: 0x080032e8,
    r3: 0x00000000,
    r12: 0x00000000,
    lr: 0x080016df,
    pc: 0x080016e2,
    xpsr: 0x61000000,
}
The pc value is the value of the Program Counter at the time of the exception and it points to the instruction that triggered the exception.

If you look at the disassembly of the program:

$ cargo objdump --bin app --release -- -d --no-show-raw-insn --print-imm-hex
(..)
ResetTrampoline:
 8000942:       movw    r0, #0xfffe
 8000946:       movt    r0, #0x3fff
 800094a:       ldr     r0, [r0]
 800094c:       b       #-0x4 <ResetTrampoline+0xa>
You can lookup the value of the program counter 0x0800094a in the disassembly. You'll see that a load operation (ldr r0, [r0] ) caused the exception. The r0 field of ExceptionFrame will tell you the value of register r0 was 0x3fff_fffe at that time.

## Interrupts

Interrupts differ from exceptions in a variety of ways but their operation and use is largely similar and they are also handled by the same interrupt controller. Whereas exceptions are defined by the Cortex-M architecture, interrupts are always vendor (and often even chip) specific implementations, both in naming and functionality.

Interrupts do allow for a lot of flexibility which needs to be accounted for when attempting to use them in an advanced way. We will not cover those uses in this book, however it is a good idea to keep the following in mind:

Interrupts have programmable priorities which determine their handlers' execution order
Interrupts can nest and preempt, i.e. execution of an interrupt handler might be interrupted by another higher-priority interrupt
In general the reason causing the interrupt to trigger needs to be cleared to prevent re-entering the interrupt handler endlessly
The general initialization steps at runtime are always the same:

Setup the peripheral(s) to generate interrupts requests at the desired occasions
Set the desired priority of the interrupt handler in the interrupt controller
Enable the interrupt handler in the interrupt controller
Similarly to exceptions, the cortex-m-rt crate exposes an interrupt attribute for declaring interrupt handlers. However, this attribute is only available when the device feature is enabled. That said, this attribute is not intended to be used directly—doing so will result in a compilation error.

Instead, you should use the re-exported version of the interrupt attribute provided by the device crate (usually generated using svd2rust). This ensures that the compiler can verify that the interrupt actually exists on the target device. The list of available interrupts—and their position in the interrupt vector table—is typically auto-generated from an SVD file by svd2rust.

use lm3s6965::interrupt; // Re-exported attribute from the device crate

// Interrupt handler for the Timer2 interrupt
#[interrupt]
fn TIMER2A() {
    // ..
    // Clear reason for the generated interrupt request
}
Interrupt handlers look like plain functions (except for the lack of arguments) similar to exception handlers. However they can not be called directly by other parts of the firmware due to the special calling conventions. It is however possible to generate interrupt requests in software to trigger a diversion to the interrupt handler.

Similar to exception handlers it is also possible to declare static mut variables inside the interrupt handlers for safe state keeping.

#[interrupt]
fn TIMER2A() {
    static mut COUNT: u32 = 0;

    // `COUNT` has type `&mut u32` and it's safe to use
    *COUNT += 1;
}
For a more detailed description about the mechanisms demonstrated here please refer to the exceptions section.

## IO

TODO Cover memory mapped I/O using registers.
