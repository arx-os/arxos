# In-depth topics
A small collection of chapters covering some more details that you might care about when writing your command line application.

## Signal handling

Processes like command line applications need to react to signals sent by the operating system. The most common example is probably Ctrl+C, the signal that typically tells a process to terminate. To handle signals in Rust programs you need to consider how you can receive these signals as well as how you can react to them.

Note: If your applications does not need to gracefully shutdown, the default handling is fine (i.e. exit immediately and let the OS cleanup resources like open file handles). In that case: No need to do what this chapter tells you!

However, for applications that need to clean up after themselves, this chapter is very relevant! For example, if your application needs to properly close network connections (saying “good bye” to the processes at the other end), remove temporary files, or reset system settings, read on.
Differences between operating systems

On Unix systems (like Linux, macOS, and FreeBSD) a process can receive signals. It can either react to them in a default (OS-provided) way, catch the signal and handle them in a program-defined way, or ignore the signal entirely.

Windows does not have signals. You can use Console Handlers to define callbacks that get executed when an event occurs. There is also structured exception handling which handles all the various types of system exceptions such as division by zero, invalid access exceptions, stack overflow, and so on

First off: Handling Ctrl+C

The ctrlc crate does just what the name suggests: It allows you to react to the user pressing Ctrl+C, in a cross-platform way. The main way to use the crate is this:


use std::{thread, time::Duration};

fn main() {
    ctrlc::set_handler(move || {
        println!("received Ctrl+C!");
    })
    .expect("Error setting Ctrl-C handler");

    // Following code does the actual work, and can be interrupted by pressing
    // Ctrl-C. As an example: Let's wait a few seconds.
    thread::sleep(Duration::from_secs(2));
}
This is, of course, not that helpful: It only prints a message but otherwise doesn’t stop the program.

In a real-world program, it’s a good idea to instead set a variable in the signal handler that you then check in various places in your program. For example, you can set an Arc<AtomicBool> (a boolean shareable between threads) in your signal handler, and in hot loops, or when waiting for a thread, you periodically check its value and break when it becomes true.

Handling other types of signals

The ctrlc crate only handles Ctrl+C, or, what on Unix systems would be called SIGINT (the “interrupt” signal). To react to more Unix signals, you should have a look at signal-hook. Its design is described in this blog post, and it is currently the library with the widest community support.

Here’s a simple example:


use signal_hook::{consts::SIGINT, iterator::Signals};
use std::{error::Error, thread, time::Duration};

fn main() -> Result<(), Box<dyn Error>> {
    let mut signals = Signals::new([SIGINT])?;

    thread::spawn(move || {
        for sig in signals.forever() {
            println!("Received signal {:?}", sig);
        }
    });

    // Following code does the actual work, and can be interrupted by pressing
    // Ctrl-C. As an example: Let's wait a few seconds.
    thread::sleep(Duration::from_secs(2));

    Ok(())
}
Using channels

Instead of setting a variable and having other parts of the program check it, you can use channels: You create a channel into which the signal handler emits a value whenever the signal is received. In your application code you use this and other channels as synchronization points between threads. Using crossbeam-channel it would look something like this:


use std::time::Duration;
use crossbeam_channel::{bounded, tick, Receiver, select};
use anyhow::Result;

fn ctrl_channel() -> Result<Receiver<()>, ctrlc::Error> {
    let (sender, receiver) = bounded(100);
    ctrlc::set_handler(move || {
        let _ = sender.send(());
    })?;

    Ok(receiver)
}

fn main() -> Result<()> {
    let ctrl_c_events = ctrl_channel()?;
    let ticks = tick(Duration::from_secs(1));

    loop {
        select! {
            recv(ticks) -> _ => {
                println!("working!");
            }
            recv(ctrl_c_events) -> _ => {
                println!();
                println!("Goodbye!");
                break;
            }
        }
    }

    Ok(())
}
Using futures and streams

If you are using tokio, you are most likely already writing your application with asynchronous patterns and an event-driven design. Instead of using crossbeam’s channels directly, you can enable signal-hook’s tokio-support feature. This allows you to call .into_async() on signal-hook’s Signals types to get a new type that implements futures::Stream.

What to do when you receive another Ctrl+C while you’re handling the first Ctrl+C

Most users will press Ctrl+C, and then give your program a few seconds to exit, or tell them what’s going on. If that doesn’t happen, they will press Ctrl+C again. The typical behavior is to have the application quit immediately.

## Using config files

Dealing with configurations can be annoying especially if you support multiple operating systems which all have their own places for short- and long-term files.

There are multiple solutions to this, some being more low-level than others.

The easiest crate to use for this is confy. It asks you for the name of your application and requires you to specify the config layout via a struct (that is Serialize, Deserialize) and it will figure out the rest!


#[derive(Debug, Serialize, Deserialize)]
struct MyConfig {
    name: String,
    comfy: bool,
    foo: i64,
}

fn main() -> Result<(), io::Error> {
    let cfg: MyConfig = confy::load("my_app")?;
    println!("{:#?}", cfg);
    Ok(())
}
This is incredibly easy to use for which you of course surrender configurability. But if a simple config is all you want, this crate might be for you!

Configuration environments

TODO

Evaluate crates that exist
Cli-args + multiple configs + env variables
Can configure do all this? Is there a nice wrapper around it?
## Exit codes

A program doesn’t always succeed. And when an error occurs, you should make sure to emit the necessary information correctly. In addition to telling the user about errors, on most systems, when a process exits, it also emits an exit code (an integer between 0 and 255 is compatible with most platforms). You should try to emit the correct code for your program’s state. For example, in the ideal case when your program succeeds, it should exit with 0.

When an error occurs, it gets a bit more complicated, though. In the wild, many tools exit with 1 when a common failure occurs. Currently, Rust sets an exit code of 101 when the process panicked. Beyond that, people have done many things in their programs.

So, what to do? The BSD ecosystem has collected a common definition for their exit codes (you can find them here). The Rust library exitcode provides these same codes, ready to be used in your application. Please see its API documentation for the possible values to use.

After you add the exitcode dependency to your Cargo.toml, you can use it like this:


fn main() {
    // ...actual work...
    match result {
        Ok(_) => {
            println!("Done!");
            std::process::exit(exitcode::OK);
        }
        Err(CustomError::CantReadConfig(e)) => {
            eprintln!("Error: {}", e);
            std::process::exit(exitcode::CONFIG);
        }
        Err(e) => {
            eprintln!("Error: {}", e);
            std::process::exit(exitcode::DATAERR);
        }
    }
}
## Communicating with humans

Make sure to read the chapter on CLI output in the tutorial first. It covers how to write output to the terminal, while this chapter will talk about what to output.

When everything is fine

It is useful to report on the application’s progress even when everything is fine. Try to be informative and concise in these messages. Don’t use overly technical terms in the logs. Remember: the application is not crashing so there’s no reason for users to look up errors.

Most importantly, be consistent in the style of communication. Use the same prefixes and sentence structure to make the logs easily skimmable.

Try to let your application output tell a story about what it’s doing and how it impacts the user. This can involve showing a timeline of steps involved or even a progress bar and indicator for long-running actions. The user should at no point get the feeling that the application is doing something mysterious that they cannot follow.

When it’s hard to tell what’s going on

When communicating non-nominal state it’s important to be consistent. A heavily logging application that doesn’t follow strict logging levels provides the same amount, or even less information than a non-logging application.

Because of this, it’s important to define the severity of events and messages that are related to it; then use consistent log levels for them. This way users can select the amount of logging themselves via --verbose flags or environment variables (like RUST_LOG).

The commonly used log crate defines the following levels (ordered by increasing severity):

trace
debug
info
warning
error
It’s a good idea to think of info as the default log level. Use it for, well, informative output. (Some applications that lean towards a more quiet output style might only show warnings and errors by default.)

Additionally, it’s always a good idea to use similar prefixes and sentence structure across log messages, making it easy to use a tool like grep to filter for them. A message should provide enough context by itself to be useful in a filtered log while not being too verbose at the same time.

Example log statements


error: could not find `Cargo.toml` in `/home/you/project/`

=> Downloading repository index
=> Downloading packages...
The following log output is taken from wasm-pack:


 [1/7] Adding WASM target...
 [2/7] Compiling to WASM...
 [3/7] Creating a pkg directory...
 [4/7] Writing a package.json...
 > [WARN]: Field `description` is missing from Cargo.toml. It is not necessary, but recommended
 > [WARN]: Field `repository` is missing from Cargo.toml. It is not necessary, but recommended
 > [WARN]: Field `license` is missing from Cargo.toml. It is not necessary, but recommended
 [5/7] Copying over your README...
 > [WARN]: origin crate has no README
 [6/7] Installing WASM-bindgen...
 > [INFO]: wasm-bindgen already installed
 [7/7] Running WASM-bindgen...
 Done in 1 second
When panicking

One aspect often forgotten is that your program also outputs something when it crashes. In Rust, “crashes” are most often “panics” (i.e., “controlled crashing” in contrast to “the operating system killed the process”). By default, when a panic occurs, a “panic handler” will print some information to the console.

For example, if you create a new binary project with cargo new --bin foo and replace the content of fn main with panic!("Hello World"), you get this when you run your program:


thread 'main' panicked at 'Hello, world!', src/main.rs:2:5
note: Run with `RUST_BACKTRACE=1` for a backtrace.
This is useful information to you, the developer. (Surprise: the program crashed because of line 2 in your main.rs file). But for a user who doesn’t even have access to the source code, this is not very valuable. In fact, it most likely is just confusing. That’s why it’s a good idea to add a custom panic handler, that provides a bit more end-user focused output.

One library that does just that is called human-panic. To add it to your CLI project, you import it and call the setup_panic!() macro at the beginning of your main function:


use human_panic::setup_panic;

fn main() {
   setup_panic!();

   panic!("Hello world")
}
This will now show a very friendly message, and tells the user what they can do:


Well, this is embarrassing.

foo had a problem and crashed. To help us diagnose the problem you can send us a crash report.

We have generated a report file at "/var/folders/n3/dkk459k908lcmkzwcmq0tcv00000gn/T/report-738e1bec-5585-47a4-8158-f1f7227f0168.toml". Submit an issue or email with the subject of "foo Crash Report" and include the report as an attachment.

- Authors: Your Name <your.name@example.com>

We take privacy seriously, and do not perform any automated error collection. In order to improve the software, we rely on people to submit reports.

Thank you kindly!
## Communicating with machines

The power of command-line tools really comes to shine when you are able to combine them. This is not a new idea: In fact, this is a sentence from the Unix philosophy:

Expect the output of every program to become the input to another, as yet unknown, program.

If our programs fulfill this expectation, our users will be happy. To make sure this works well, we should provide not just pretty output for humans, but also a version tailored to what other programs need. Let’s see how we can do this.

Note: Make sure to read the chapter on CLI output in the tutorial first. It covers how to write output to the terminal.
Who’s reading this?

The first question to ask is: Is our output for a human in front of a colorful terminal, or for another program? To answer this, we can use the IsTerminal trait:


use std::io::IsTerminal;

if std::io::stdout().is_terminal() {
    println!("I'm a terminal");
} else {
    println!("I'm not");
}
Depending on who will read our output, we can then add extra information. Humans tend to like colors, for example, if you run ls in a random Rust project, you might see something like this:


$ ls
CODE_OF_CONDUCT.md   LICENSE-APACHE       examples
CONTRIBUTING.md      LICENSE-MIT          proptest-regressions
Cargo.lock           README.md            src
Cargo.toml           convey_derive        target
Because this style is made for humans, in most configurations it’ll even print some of the names (like src) in color to show that they are directories. If you instead pipe this to a file, or a program like cat, ls will adapt its output. Instead of using columns that fit my terminal window it will print every entry on its own line. It will also not emit any colors.


$ ls | cat
CODE_OF_CONDUCT.md
CONTRIBUTING.md
Cargo.lock
Cargo.toml
LICENSE-APACHE
LICENSE-MIT
README.md
convey_derive
examples
proptest-regressions
src
target
Easy output formats for machines

Historically, the only type of output command-line tools produced were strings. This is usually fine for people in front of terminals, who are able to read text and reason about its meaning. Other programs usually don’t have that ability, though: The only way for them to understand the output of a tool like ls is if the author of the program included a parser that happens to work for whatever ls outputs.

This often means that output was limited to what is easy to parse. Formats like TSV (tab-separated values), where each record is on its own line, and each line contains tab-separated content, are very popular. These simple formats based on lines of text allow tools like grep to be used on the output of tools like ls. | grep Cargo doesn’t care if your lines are from ls or file, it will just filter line by line.

The downside of this is that you can’t use an easy grep invocation to filter all the directories that ls gave you. For that, each directory item would need to carry additional data.

JSON output for machines

Tab-separated values is a simple way to output structured data but it requires the other program to know which fields to expect (and in which order) and it’s difficult to output messages of different types. For example, let’s say our program wanted to message the consumer that it is currently waiting for a download, and afterwards output a message describing the data it got. Those are very different kinds of messages and trying to unify them in a TSV output would require us to invent a way to differentiate them. Same when we wanted to print a message that contains two lists of items of varying lengths.

Still, it’s a good idea to choose a format that is easily parsable in most programming languages/environments. Thus, over the last years a lot of applications gained the ability to output their data in JSON. It’s simple enough that parsers exist in practically every language yet powerful enough to be useful in a lot of cases. While its a text format that can be read by humans, a lot of people have also worked on implementations that are very fast at parsing JSON data and serializing data to JSON.

In the description above, we’ve talked about “messages” being written by our program. This is a good way of thinking about the output: Your program doesn’t necessarily only output one blob of data but may in fact emit a lot of different information while it is running. One easy way to support this approach when outputting JSON is to write one JSON document per message and to put each JSON document on new line (sometimes called Line-delimited JSON). This can make implementations as simple as using a regular println!.

Here’s a simple example, using the json! macro from serde_json to quickly write valid JSON in your Rust source code:


use clap::Parser;
use serde_json::json;

/// Search for a pattern in a file and display the lines that contain it.
#[derive(Parser)]
struct Cli {
    /// Output JSON instead of human readable messages
    #[arg(long = "json")]
    json: bool,
}

fn main() {
    let args = Cli::parse();
    if args.json {
        println!(
            "{}",
            json!({
                "type": "message",
                "content": "Hello world",
            })
        );
    } else {
        println!("Hello world");
    }
}
And here is the output:


$ cargo run -q
Hello world
$ cargo run -q -- --json
{"content":"Hello world","type":"message"}
(Running cargo with -q suppresses its usual output. The arguments after -- are passed to our program.)

Practical example: ripgrep

ripgrep is a replacement for grep or ag, written in Rust. By default it will produce output like this:


$ rg default
src/lib.rs
37:    Output::default()

src/components/span.rs
6:    Span::default()
But given --json it will print:


$ rg default --json
{"type":"begin","data":{"path":{"text":"src/lib.rs"}}}
{"type":"match","data":{"path":{"text":"src/lib.rs"},"lines":{"text":"    Output::default()\n"},"line_number":37,"absolute_offset":761,"submatches":[{"match":{"text":"default"},"start":12,"end":19}]}}
{"type":"end","data":{"path":{"text":"src/lib.rs"},"binary_offset":null,"stats":{"elapsed":{"secs":0,"nanos":137622,"human":"0.000138s"},"searches":1,"searches_with_match":1,"bytes_searched":6064,"bytes_printed":256,"matched_lines":1,"matches":1}}}
{"type":"begin","data":{"path":{"text":"src/components/span.rs"}}}
{"type":"match","data":{"path":{"text":"src/components/span.rs"},"lines":{"text":"    Span::default()\n"},"line_number":6,"absolute_offset":117,"submatches":[{"match":{"text":"default"},"start":10,"end":17}]}}
{"type":"end","data":{"path":{"text":"src/components/span.rs"},"binary_offset":null,"stats":{"elapsed":{"secs":0,"nanos":22025,"human":"0.000022s"},"searches":1,"searches_with_match":1,"bytes_searched":5221,"bytes_printed":277,"matched_lines":1,"matches":1}}}
{"data":{"elapsed_total":{"human":"0.006995s","nanos":6994920,"secs":0},"stats":{"bytes_printed":533,"bytes_searched":11285,"elapsed":{"human":"0.000160s","nanos":159647,"secs":0},"matched_lines":2,"matches":2,"searches":2,"searches_with_match":2}},"type":"summary"}
As you can see, each JSON document is an object (map) containing a type field. This would allow us to write a simple frontend for rg that reads these documents as they come in and show the matches (as well the files they are in) even while ripgrep is still searching.

Note: This is how Visual Studio Code uses ripgrep for its code search.
How to deal with input piped into us

Let’s say we have a program that reads the number of words in a file:


use clap::Parser;
use std::path::PathBuf;

/// Count the number of lines in a file
#[derive(Parser)]
#[command(arg_required_else_help = true)]
struct Cli {
    /// The path to the file to read
    file: PathBuf,
}

fn main() {
    let args = Cli::parse();
    let mut word_count = 0;
    let file = args.file;

    for line in std::fs::read_to_string(&file).unwrap().lines() {
        word_count += line.split(' ').count();
    }

    println!("Words in {}: {}", file.to_str().unwrap(), word_count)
}
It takes the path to a file, reads it line by line, and counts the number of words separated by a space.

When you run it, it outputs the total words in the file:


$ cargo run README.md
Words in README.md: 47
But what if we wanted to count the number of words piped into the program? Rust programs can read data passed in via stdin with the Stdin struct which you can obtain via the stdin function from the standard library. Similar to reading the lines of a file, it can read the lines from stdin.

Here’s a program that counts the words of what’s piped in via stdin


use clap::{CommandFactory, Parser};
use std::{
    fs::File,
    io::{stdin, BufRead, BufReader, IsTerminal},
    path::PathBuf,
};

/// Count the number of lines in a file or stdin
#[derive(Parser)]
#[command(arg_required_else_help = true)]
struct Cli {
    /// The path to the file to read, use - to read from stdin (must not be a tty)
    file: PathBuf,
}

fn main() {
    let args = Cli::parse();

    let word_count;
    let mut file = args.file;

    if file == PathBuf::from("-") {
        if stdin().is_terminal() {
            Cli::command().print_help().unwrap();
            ::std::process::exit(2);
        }

        file = PathBuf::from("<stdin>");
        word_count = words_in_buf_reader(BufReader::new(stdin().lock()));
    } else {
        word_count = words_in_buf_reader(BufReader::new(File::open(&file).unwrap()));
    }

    println!("Words from {}: {}", file.to_string_lossy(), word_count)
}

fn words_in_buf_reader<R: BufRead>(buf_reader: R) -> usize {
    let mut count = 0;
    for line in buf_reader.lines() {
        count += line.unwrap().split(' ').count()
    }
    count
}
If you run that program with text piped in, with - representing the intent to read from stdin, it’ll output the word count:


$ echo "hi there friend" | cargo run -- -
Words from stdin: 3
It requires that stdin is not interactive because we’re expecting input that’s piped through to the program, not text that’s typed in at runtime. If stdin is a tty, it outputs the help docs so that it’s clear why it doesn’t work.

## Rendering documentation for your CLI apps

Documentation for CLIs usually consists of a --help section in the command and a manual (man) page.

Both can be automatically generated when using clap, via clap_mangen crate.


#[derive(Parser)]
pub struct Head {
    /// file to load
    pub file: PathBuf,
    /// how many lines to print
    #[arg(short = "n", default_value = "5")]
    pub count: usize,
}
Secondly, you need to use a build.rs to generate the manual file at compile time from the definition of your app in code.

There are a few things to keep in mind (such as how you want to package your binary) but for now we simply put the man file next to our src folder.


use clap::CommandFactory;

#[path="src/cli.rs"]
mod cli;

fn main() -> std::io::Result<()> {
    let out_dir = std::path::PathBuf::from(std::env::var_os("OUT_DIR").ok_or_else(|| std::io::ErrorKind::NotFound)?);
    let cmd = cli::Head::command();

    let man = clap_mangen::Man::new(cmd);
    let mut buffer: Vec<u8> = Default::default();
    man.render(&mut buffer)?;

    std::fs::write(out_dir.join("head.1"), buffer)?;

    Ok(())
}
When you now compile your application there will be a head.1 file in your project directory.

If you open that in man you’ll be able to admire your free documentation.
