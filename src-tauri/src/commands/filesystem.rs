use std::fs;
use tauri::{api::dialog::FileDialogBuilder, Window};

#[tauri::command]
pub fn pick_file(window: Window) -> Option<String> {
    let (tx, rx) = std::sync::mpsc::channel();
    FileDialogBuilder::new().pick_file(move |file| {
        if let Some(path) = file {
            tx.send(Some(path.display().to_string())).ok();
        } else {
            tx.send(None).ok();
        }
    });
    rx.recv().unwrap_or(None)
}

#[tauri::command]
pub fn read_file(path: String) -> Result<String, String> {
    fs::read_to_string(&path).map_err(|e| format!("Read error: {}", e))
}

#[tauri::command]
pub fn write_file(path: String, contents: String) -> Result<(), String> {
    fs::write(&path, contents).map_err(|e| format!("Write error: {}", e))
}
