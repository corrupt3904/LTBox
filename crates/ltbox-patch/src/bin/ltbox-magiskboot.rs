//! Standalone host for library consumers and integration tests.
fn main() {
    std::process::exit(ltbox_patch::boot::dispatch_magiskboot_helper().unwrap_or(2));
}
