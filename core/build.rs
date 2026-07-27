fn main() {
    #[cfg(feature = "uniffi")]
    {
        uniffi::generate_scaffolding("src/arxos.udl").unwrap();
    }
}
