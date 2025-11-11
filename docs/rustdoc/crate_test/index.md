# test Crate Experimental APIs
Support code for rustc’s built in unit-test and micro-benchmarking framework.

Almost all user code will only be interested in Bencher and black_box. All other interactions (such as writing tests and benchmarks themselves) should be done via the #[test] and #[bench] attributes.

See the Testing Chapter of the book for more details.
Re-exports

pub use self::bench::Bencher;Experimental
pub use self::bench::black_box;Experimental
pub use self::ColorConfig::*;Experimental
pub use self::types::TestName::*;Experimental
pub use NamePadding::*;Experimental
pub use TestFn::*;Experimental
pub use TestName::*;Experimental
Modules

benchExperimental
Benchmarking module.
statsExperimental
testExperimental
Structs

OptionsExperimental
Options for the test run defined by the caller (instead of CLI arguments). In case we want to add other options as well, just add them in this struct.
TestDescExperimental
TestDescAndFnExperimental
TestIdExperimental
TestOptsExperimental
Enums

ColorConfigExperimental
Whether should console output be colored or not
NamePaddingExperimental
OutputFormatExperimental
Format of the test results output
RunIgnoredExperimental
Whether ignored test should be run or not
ShouldPanicExperimental
Whether test is expected to panic or not
TestFnExperimental
TestNameExperimental
TestTypeExperimental
Type of the test according to the Rust book conventions.
Constants

ERROR_EXIT_CODEExperimental
Process exit code to be used to indicate test failures.
Functions

assert_test_resultExperimental
Invoked when unit tests terminate. Returns Result::Err if the test is considered a failure. By default, invokes report() and checks for a 0 result.
convert_benchmarks_to_testsExperimental
filter_testsExperimental
print_merged_doctests_timesExperimental
Public API used by rustdoc to display the total and compilation times in the expected format.
run_testExperimental
run_testsExperimental
run_tests_consoleExperimental
A simple console test runner. Runs provided tests reporting process and results to the stdout.
test_mainExperimental
test_main_staticExperimental
A variant optimized for invocation with a static test vector. This will panic (intentionally) when fed any dynamic tests.
test_main_static_abortExperimental
A variant optimized for invocation with a static test vector. This will panic (intentionally) when fed any dynamic tests.
test_main_with_exit_callbackExperimental
