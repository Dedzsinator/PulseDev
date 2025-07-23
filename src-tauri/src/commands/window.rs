use tauri::Window;

#[tauri::command]
pub fn minimize_window(window: Window) {
    let _ = window.minimize();
}

#[tauri::command]
pub fn maximize_window(window: Window) {
    let _ = window.maximize();
}

#[tauri::command]
pub fn close_window(window: Window) {
    let _ = window.close();
}

#[tauri::command]
pub fn show_window(window: Window) {
    let _ = window.show();
}

#[tauri::command]
pub fn hide_window(window: Window) {
    let _ = window.hide();
}
