//! Acquire the application guard before starting workers or shared workspaces.
use fs2::FileExt;
use std::{
    fs::{File, OpenOptions},
    io,
    path::Path,
    time::{Duration, Instant},
};

pub(crate) fn acquire(path: &Path, wait_for_update: bool) -> io::Result<Option<File>> {
    let file = OpenOptions::new()
        .create(true)
        .truncate(false)
        .read(true)
        .write(true)
        .open(path)?;
    let deadline = Instant::now() + Duration::from_secs(15);
    loop {
        match file.try_lock_exclusive() {
            Ok(()) => return Ok(Some(file)),
            Err(error) if error.raw_os_error() == fs2::lock_contended_error().raw_os_error() => {
                if wait_for_update && Instant::now() < deadline {
                    std::thread::sleep(Duration::from_millis(100));
                } else {
                    return Ok(None);
                }
            }
            Err(error) => return Err(error),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn lock_failure_is_distinct_from_an_existing_instance() {
        let dir = tempfile::tempdir().unwrap();
        assert!(acquire(dir.path(), false).is_err());
        let path = dir.path().join("instance.lock");
        let first = acquire(&path, false).unwrap().unwrap();
        assert!(acquire(&path, false).unwrap().is_none());
        drop(first);
        assert!(acquire(&path, false).unwrap().is_some());
    }
}
