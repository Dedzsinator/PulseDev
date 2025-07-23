use tauri::api::notification::Notification;

#[tauri::command]
pub fn send_notification(title: String, body: String) -> Result<(), String> {
    Notification::new("dev.pulse.ccm")
        .title(&title)
        .body(&body)
        .show()
        .map_err(|e| format!("Notification error: {}", e))
}
