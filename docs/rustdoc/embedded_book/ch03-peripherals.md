# Peripherals
What are Peripherals?

Most Microcontrollers have more than just a CPU, RAM, or Flash Memory - they contain sections of silicon which are used for interacting with systems outside of the microcontroller, as well as directly and indirectly interacting with their surroundings in the world via sensors, motor controllers, or human interfaces such as a display or keyboard. These components are collectively known as Peripherals.

These peripherals are useful because they allow a developer to offload processing to them, avoiding having to handle everything in software. Similar to how a desktop developer would offload graphics processing to a video card, embedded developers can offload some tasks to peripherals allowing the CPU to spend its time doing something else important, or doing nothing in order to save power.

If you look at the main circuit board in an old-fashioned home computer from the 1970s or 1980s (and actually, the desktop PCs of yesterday are not so far removed from the embedded systems of today) you would expect to see:

A processor
A RAM chip
A ROM chip
An I/O controller
The RAM chip, ROM chip and I/O controller (the peripheral in this system) would be joined to the processor through a series of parallel traces known as a 'bus'. This bus carries address information, which selects which device on the bus the processor wishes to communicate with, and a data bus which carries the actual data. In our embedded microcontrollers, the same principles apply - it's just that everything is packed on to a single piece of silicon.

However, unlike graphics cards, which typically have a Software API like Vulkan, Metal, or OpenGL, peripherals are exposed to our Microcontroller with a hardware interface, which is mapped to a chunk of the memory.

Linear and Real Memory Space

On a microcontroller, writing some data to some other arbitrary address, such as 0x4000_0000 or 0x0000_0000, may also be a completely valid action.

On a desktop system, access to memory is tightly controlled by the MMU, or Memory Management Unit. This component has two major responsibilities: enforcing access permission to sections of memory (preventing one process from reading or modifying the memory of another process); and re-mapping segments of the physical memory to virtual memory ranges used in software. Microcontrollers do not typically have an MMU, and instead only use real physical addresses in software.

Although 32 bit microcontrollers have a real and linear address space from 0x0000_0000, and 0xFFFF_FFFF, they generally only use a few hundred kilobytes of that range for actual memory. This leaves a significant amount of address space remaining. In earlier chapters, we were talking about RAM being located at address 0x2000_0000. If our RAM was 64 KiB long (i.e. with a maximum address of 0xFFFF) then addresses 0x2000_0000 to 0x2000_FFFF would correspond to our RAM. When we write to a variable which lives at address 0x2000_1234, what happens internally is that some logic detects the upper portion of the address (0x2000 in this example) and then activates the RAM so that it can act upon the lower portion of the address (0x1234 in this case). On a Cortex-M we also have our Flash ROM mapped in at address 0x0000_0000 up to, say, address 0x0007_FFFF (if we have a 512 KiB Flash ROM). Rather than ignore all remaining space between these two regions, Microcontroller designers instead mapped the interface for peripherals in certain memory locations. This ends up looking something like this:



Nordic nRF52832 Datasheet (pdf)

Memory Mapped Peripherals

Interaction with these peripherals is simple at a first glance - write the right data to the correct address. For example, sending a 32 bit word over a serial port could be as direct as writing that 32 bit word to a certain memory address. The Serial Port Peripheral would then take over and send out the data automatically.

Configuration of these peripherals works similarly. Instead of calling a function to configure a peripheral, a chunk of memory is exposed which serves as the hardware API. Write 0x8000_0000 to a SPI Frequency Configuration Register, and the SPI port will send data at 8 Megabits per second. Write 0x0200_0000 to the same address, and the SPI port will send data at 125 Kilobits per second. These configuration registers look a little bit like this:



Nordic nRF52832 Datasheet (pdf)

This interface is how interactions with the hardware are made, no matter what language is used, whether that language is Assembly, C, or Rust.

A First Attempt

The Registers

Let's look at the 'SysTick' peripheral - a simple timer which comes with every Cortex-M processor core. Typically you'll be looking these up in the chip manufacturer's data sheet or Technical Reference Manual, but this example is common to all ARM Cortex-M cores, let's look in the ARM reference manual. We see there are four registers:

Offset	Name	Description	Width
0x00	SYST_CSR	Control and Status Register	32 bits
0x04	SYST_RVR	Reload Value Register	32 bits
0x08	SYST_CVR	Current Value Register	32 bits
0x0C	SYST_CALIB	Calibration Value Register	32 bits
The C Approach

In Rust, we can represent a collection of registers in exactly the same way as we do in C - with a struct.

#[repr(C)]
struct SysTick {
    pub csr: u32,
    pub rvr: u32,
    pub cvr: u32,
    pub calib: u32,
}
The qualifier #[repr(C)] tells the Rust compiler to lay this structure out like a C compiler would. That's very important, as Rust allows structure fields to be re-ordered, while C does not. You can imagine the debugging we'd have to do if these fields were silently re-arranged by the compiler! With this qualifier in place, we have our four 32-bit fields which correspond to the table above. But of course, this struct is of no use by itself - we need a variable.

let systick = 0xE000_E010 as *mut SysTick;
let time = unsafe { (*systick).cvr };
Volatile Accesses

Now, there are a couple of problems with the approach above.

We have to use unsafe every time we want to access our Peripheral.
We've got no way of specifying which registers are read-only or read-write.
Any piece of code anywhere in your program could access the hardware through this structure.
Most importantly, it doesn't actually work...
Now, the problem is that compilers are clever. If you make two writes to the same piece of RAM, one after the other, the compiler can notice this and just skip the first write entirely. In C, we can mark variables as volatile to ensure that every read or write occurs as intended. In Rust, we instead mark the accesses as volatile, not the variable.

let systick = unsafe { &mut *(0xE000_E010 as *mut SysTick) };
let time = unsafe { core::ptr::read_volatile(&mut systick.cvr) };
So, we've fixed one of our four problems, but now we have even more unsafe code! Fortunately, there's a third party crate which can help - volatile_register.

use volatile_register::{RW, RO};

#[repr(C)]
struct SysTick {
    pub csr: RW<u32>,
    pub rvr: RW<u32>,
    pub cvr: RW<u32>,
    pub calib: RO<u32>,
}

fn get_systick() -> &'static mut SysTick {
    unsafe { &mut *(0xE000_E010 as *mut SysTick) }
}

fn get_time() -> u32 {
    let systick = get_systick();
    systick.cvr.read()
}
Now, the volatile accesses are performed automatically through the read and write methods. It's still unsafe to perform writes, but to be fair, hardware is a bunch of mutable state and there's no way for the compiler to know whether these writes are actually safe, so this is a good default position.

The Rusty Wrapper

We need to wrap this struct up into a higher-layer API that is safe for our users to call. As the driver author, we manually verify the unsafe code is correct, and then present a safe API for our users so they don't have to worry about it (provided they trust us to get it right!).

One example might be:

use volatile_register::{RW, RO};

pub struct SystemTimer {
    p: &'static mut RegisterBlock
}

#[repr(C)]
struct RegisterBlock {
    pub csr: RW<u32>,
    pub rvr: RW<u32>,
    pub cvr: RW<u32>,
    pub calib: RO<u32>,
}

impl SystemTimer {
    pub fn new() -> SystemTimer {
        SystemTimer {
            p: unsafe { &mut *(0xE000_E010 as *mut RegisterBlock) }
        }
    }

    pub fn get_time(&self) -> u32 {
        self.p.cvr.read()
    }

    pub fn set_reload(&mut self, reload_value: u32) {
        unsafe { self.p.rvr.write(reload_value) }
    }
}

pub fn example_usage() -> String {
    let mut st = SystemTimer::new();
    st.set_reload(0x00FF_FFFF);
    format!("Time is now 0x{:08x}", st.get_time())
}
Now, the problem with this approach is that the following code is perfectly acceptable to the compiler:

fn thread1() {
    let mut st = SystemTimer::new();
    st.set_reload(2000);
}

fn thread2() {
    let mut st = SystemTimer::new();
    st.set_reload(1000);
}
Our &mut self argument to the set_reload function checks that there are no other references to that particular SystemTimer struct, but they don't stop the user creating a second SystemTimer which points to the exact same peripheral! Code written in this fashion will work if the author is diligent enough to spot all of these 'duplicate' driver instances, but once the code is spread out over multiple modules, drivers, developers, and days, it gets easier and easier to make these kinds of mistakes.

Mutable Global State

Unfortunately, hardware is basically nothing but mutable global state, which can feel very frightening for a Rust developer. Hardware exists independently from the structures of the code we write, and can be modified at any time by the real world.

What should our rules be?

How can we reliably interact with these peripherals?

Always use volatile methods to read or write to peripheral memory, as it can change at any time
In software, we should be able to share any number of read-only accesses to these peripherals
If some software should have read-write access to a peripheral, it should hold the only reference to that peripheral
## The Borrow Checker

The last two of these rules sound suspiciously similar to what the Borrow Checker does already!

Imagine if we could pass around ownership of these peripherals, or offer immutable or mutable references to them?

Well, we can, but for the Borrow Checker, we need to have exactly one instance of each peripheral, so Rust can handle this correctly. Well, luckily in the hardware, there is only one instance of any given peripheral, but how can we expose that in the structure of our code?

## Singletons

In software engineering, the singleton pattern is a software design pattern that restricts the instantiation of a class to one object.

Wikipedia: Singleton Pattern

But why can't we just use global variable(s)?

We could make everything a public static, like this

static mut THE_SERIAL_PORT: SerialPort = SerialPort;

fn main() {
    let _ = unsafe {
        THE_SERIAL_PORT.read_speed();
    };
}
But this has a few problems. It is a mutable global variable, and in Rust, these are always unsafe to interact with. These variables are also visible across your whole program, which means the borrow checker is unable to help you track references and ownership of these variables.

How do we do this in Rust?

Instead of just making our peripheral a global variable, we might instead decide to make a structure, in this case called PERIPHERALS, which contains an Option<T> for each of our peripherals.

struct Peripherals {
    serial: Option<SerialPort>,
}
impl Peripherals {
    fn take_serial(&mut self) -> SerialPort {
        let p = replace(&mut self.serial, None);
        p.unwrap()
    }
}
static mut PERIPHERALS: Peripherals = Peripherals {
    serial: Some(SerialPort),
};
This structure allows us to obtain a single instance of our peripheral. If we try to call take_serial() more than once, our code will panic!

fn main() {
    let serial_1 = unsafe { PERIPHERALS.take_serial() };
    // This panics!
    // let serial_2 = unsafe { PERIPHERALS.take_serial() };
}
Although interacting with this structure is unsafe, once we have the SerialPort it contained, we no longer need to use unsafe, or the PERIPHERALS structure at all.

This has a small runtime overhead because we must wrap the SerialPort structure in an option, and we'll need to call take_serial() once, however this small up-front cost allows us to leverage the borrow checker throughout the rest of our program.

Existing library support

Although we created our own Peripherals structure above, it is not necessary to do this for your code. the cortex_m crate contains a macro called singleton!() that will perform this action for you.

use cortex_m::singleton;

fn main() {
    // OK if `main` is executed only once
    let x: &'static mut bool =
        singleton!(: bool = false).unwrap();
}
cortex_m docs

Additionally, if you use cortex-m-rtic, the entire process of defining and obtaining these peripherals are abstracted for you, and you are instead handed a Peripherals structure that contains a non-Option<T> version of all of the items you define.

// cortex-m-rtic v0.5.x
#[rtic::app(device = lm3s6965, peripherals = true)]
const APP: () = {
    #[init]
    fn init(cx: init::Context) {
        static mut X: u32 = 0;
         
        // Cortex-M peripherals
        let core: cortex_m::Peripherals = cx.core;
        
        // Device specific peripherals
        let device: lm3s6965::Peripherals = cx.device;
    }
}
But why?

But how do these Singletons make a noticeable difference in how our Rust code works?

impl SerialPort {
    const SER_PORT_SPEED_REG: *mut u32 = 0x4000_1000 as _;

    fn read_speed(
        &self // <------ This is really, really important
    ) -> u32 {
        unsafe {
            ptr::read_volatile(Self::SER_PORT_SPEED_REG)
        }
    }
}
There are two important factors in play here:

Because we are using a singleton, there is only one way or place to obtain a SerialPort structure
To call the read_speed() method, we must have ownership or a reference to a SerialPort structure
These two factors put together means that it is only possible to access the hardware if we have appropriately satisfied the borrow checker, meaning that at no point do we have multiple mutable references to the same hardware!

fn main() {
    // missing reference to `self`! Won't work.
    // SerialPort::read_speed();

    let serial_1 = unsafe { PERIPHERALS.take_serial() };

    // you can only read what you have access to
    let _ = serial_1.read_speed();
}
Treat your hardware like data

Additionally, because some references are mutable, and some are immutable, it becomes possible to see whether a function or method could potentially modify the state of the hardware. For example,

This is allowed to change hardware settings:

fn setup_spi_port(
    spi: &mut SpiPort,
    cs_pin: &mut GpioPin
) -> Result<()> {
    // ...
}
This isn't:

fn read_button(gpio: &GpioPin) -> bool {
    // ...
}
This allows us to enforce whether code should or should not make changes to hardware at compile time, rather than at runtime. As a note, this generally only works across one application, but for bare metal systems, our software will be compiled into a single application, so this is not usually a restriction.
