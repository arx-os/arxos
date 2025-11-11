# Runtime Feature Detection APIs
Run-time feature detection for the Rust standard library.

To detect whether a feature is enabled in the system running the binary use one of the appropriate macro for the target:

x86 and x86_64: is_x86_feature_detected
arm: is_arm_feature_detected
aarch64: is_aarch64_feature_detected
riscv: is_riscv_feature_detected
mips: is_mips_feature_detected
mips64: is_mips64_feature_detected
powerpc: is_powerpc_feature_detected
powerpc64: is_powerpc64_feature_detected
loongarch: is_loongarch_feature_detected
s390x: is_s390x_feature_detected
Macros

detect_featureExperimental
is_aarch64_feature_detectedExperimentalAArch64 or target_arch="arm64ec"
This macro tests, at runtime, whether an aarch64 feature is enabled on aarch64 platforms. Currently most features are only supported on linux-based platforms.
is_arm_feature_detectedExperimentalARM
Checks if arm feature is enabled.
is_loongarch_feature_detectedExperimentalLoongArch LA32 or LoongArch LA64
Checks if loongarch feature is enabled. Supported arguments are:
is_mips64_feature_detectedExperimentalMIPS-64
Checks if mips64 feature is enabled.
is_mips_feature_detectedExperimentalMIPS
Checks if mips feature is enabled.
is_powerpc64_feature_detectedExperimentalPowerPC-64
Checks if powerpc feature is enabled.
is_powerpc_feature_detectedExperimentalPowerPC
Checks if powerpc feature is enabled.
is_riscv_feature_detectedExperimentalRISC-V RV32 or RISC-V RV64
A macro to test at runtime whether instruction sets are available on RISC-V platforms.
is_s390x_feature_detectedExperimentals390x
Checks if s390x feature is enabled.
is_x86_feature_detectedExperimentalx86 or x86-64
A macro to test at runtime whether a CPU feature is available on x86/x86-64 platforms.
