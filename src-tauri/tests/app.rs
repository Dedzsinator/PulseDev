#![cfg(test)]
use tauri_test::{assert, Builder};

#[test]
fn test_get_dnd_status() {
    let mut app = Builder::new().build();
    let result = app.command("get_dnd_status", None::<()>);
    assert!(result.is_ok());
}

#[test]
fn test_set_dnd_status() {
    let mut app = Builder::new().build();
    let result = app.command("set_dnd_status", Some(serde_json::json!({"enabled": true})));
    assert!(result.is_ok());
}

#[test]
fn test_send_notification() {
    let mut app = Builder::new().build();
    let result = app.command(
        "send_notification",
        Some(serde_json::json!({"title": "Test", "body": "Hello from test"})),
    );
    assert!(result.is_ok());
}

#[test]
fn test_read_write_file() {
    let mut app = Builder::new().build();
    let path = "/tmp/pulsedev_test_file.txt";
    let write_result = app.command(
        "write_file",
        Some(serde_json::json!({"path": path, "contents": "test content"})),
    );
    assert!(write_result.is_ok());
    let read_result = app.command("read_file", Some(serde_json::json!({"path": path})));
    assert!(read_result.is_ok());
    let content: String = serde_json::from_value(read_result.unwrap()).unwrap();
    assert_eq!(content, "test content");
}
