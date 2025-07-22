// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::Manager;

#[tauri::command]
fn send_notification(title: String, body: String) {
    tauri::api::notification::Notification::new("dev.pulse.ccm")
        .title(&title)
        .body(&body)
        .show()
        .unwrap();
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![send_notification])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
