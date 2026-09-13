use std::process::Command;

#[test]
fn helper_isolates_working_directories_and_environment() {
    let parent_dir = std::env::current_dir().unwrap();
    let parent_env = std::env::var_os("KEEPVERITY");
    let directories = [tempfile::tempdir().unwrap(), tempfile::tempdir().unwrap()];
    std::thread::scope(|scope| {
        for (index, directory) in directories.iter().enumerate() {
            scope.spawn(move || {
                std::fs::write(directory.path().join("input"), vec![index as u8; 1024]).unwrap();
                let status = Command::new(env!("CARGO_BIN_EXE_ltbox-magiskboot"))
                    .args([
                        "--ltbox-internal-magiskboot",
                        "compress=gzip",
                        "input",
                        "output.gz",
                    ])
                    .env("KEEPVERITY", if index == 0 { "true" } else { "false" })
                    .current_dir(directory.path())
                    .status()
                    .unwrap();
                assert!(status.success());
                assert!(directory.path().join("output.gz").is_file());
            });
        }
    });
    assert_eq!(std::env::current_dir().unwrap(), parent_dir);
    assert_eq!(std::env::var_os("KEEPVERITY"), parent_env);
}
