// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
use commands::{dnd::*, filesystem::*, notifications::*, tray::*, window::*};
use tauri::{Manager, SystemTrayEvent};

fn main() {
    let tray = create_tray();
    tauri::Builder::default()
        .system_tray(tray)
        .on_system_tray_event(|app, event| {
            handle_tray_event(app, event);
        })
        .invoke_handler(tauri::generate_handler![
            send_notification,
            pick_file,
            read_file,
            write_file,
            get_dnd_status,
            set_dnd_status,
            minimize_window,
            maximize_window,
            close_window,
            show_window,
            hide_window
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
