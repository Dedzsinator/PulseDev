// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::fs;
use tauri::api::dialog::FileDialogBuilder;
use tauri::{Manager, Window};

#[tauri::command]
fn send_notification(title: String, body: String) {
    tauri::api::notification::Notification::new("dev.pulse.ccm")
        .title(&title)
        .body(&body)
        .show()
        .unwrap();
}

#[tauri::command]
fn pick_file(window: Window) -> Option<String> {
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
fn read_file(path: String) -> Result<String, String> {
    fs::read_to_string(&path).map_err(|e| e.to_string())
}

#[tauri::command]
fn write_file(path: String, contents: String) -> Result<(), String> {
    fs::write(&path, contents).map_err(|e| e.to_string())
}

#[tauri::command]
fn get_dnd_status() -> bool {
    // Placeholder: always return false (not in DND)
    false
}

#[tauri::command]
fn set_dnd_status(_enabled: bool) -> bool {
    // Placeholder: just log and return the value
    // In a real implementation, call platform-specific APIs
    true
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            send_notification,
            pick_file,
            read_file,
            write_file,
            get_dnd_status,
            set_dnd_status
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
