use tauri::api::log::LogTarget;

#[tauri::command]
pub fn get_dnd_status() -> bool {
    #[cfg(target_os = "macos")]
    {
        // macOS: Use AppleScript to check DND status (macOS 12+)
        use std::process::Command;
        let output = Command::new("defaults")
            .arg("-currentHost")
            .arg("read")
            .arg("com.apple.notificationcenterui")
            .arg("doNotDisturb")
            .output();
        if let Ok(out) = output {
            let stdout = String::from_utf8_lossy(&out.stdout);
            return stdout.trim() == "1";
        }
        false
    }
    #[cfg(target_os = "windows")]
    {
        // Windows: Query Focus Assist (Quiet Hours) from registry
        use std::process::Command;
        let output = Command::new("reg")
            .args([
                "query",
                "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings",
                "/v",
                "NOC_GLOBAL_SETTING_TOASTS_ENABLED",
            ])
            .output();
        if let Ok(out) = output {
            let stdout = String::from_utf8_lossy(&out.stdout);
            // If value is 0, DND is ON; if 1, DND is OFF
            if stdout.contains("0x0") {
                return true;
            }
        }
        false
    }
    #[cfg(target_os = "linux")]
    {
        // Linux: Query D-Bus for org.gnome.SessionManager (GNOME)
        use std::process::Command;
        let output = Command::new("gdbus")
            .args([
                "call",
                "--session",
                "--dest",
                "org.gnome.SessionManager",
                "--object-path",
                "/org/gnome/SessionManager/Presence",
                "--method",
                "org.gnome.SessionManager.Presence.GetStatus",
            ])
            .output();
        if let Ok(out) = output {
            let stdout = String::from_utf8_lossy(&out.stdout);
            // 0 = available, 2 = DND
            if stdout.contains("2") {
                return true;
            }
        }
        false
    }
    #[cfg(not(any(target_os = "macos", target_os = "windows", target_os = "linux")))]
    {
        false
    }
}

#[tauri::command]
pub fn set_dnd_status(enabled: bool) -> bool {
    #[cfg(target_os = "macos")]
    {
        // macOS: Use AppleScript to toggle DND (macOS 12+)
        use std::process::Command;
        let value = if enabled { "1" } else { "0" };
        let output = Command::new("defaults")
            .arg("-currentHost")
            .arg("write")
            .arg("com.apple.notificationcenterui")
            .arg("doNotDisturb")
            .arg(value)
            .output();
        return output.map(|o| o.status.success()).unwrap_or(false);
    }
    #[cfg(target_os = "windows")]
    {
        // Windows: Set Focus Assist (Quiet Hours) via registry
        use std::process::Command;
        let value = if enabled { "0" } else { "1" };
        let output = Command::new("reg")
            .args([
                "add",
                "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings",
                "/v",
                "NOC_GLOBAL_SETTING_TOASTS_ENABLED",
                "/t",
                "REG_DWORD",
                "/d",
                value,
                "/f",
            ])
            .output();
        return output.map(|o| o.status.success()).unwrap_or(false);
    }
    #[cfg(target_os = "linux")]
    {
        // Linux: Set DND via D-Bus (GNOME)
        use std::process::Command;
        let value = if enabled { "2" } else { "0" };
        let output = Command::new("gdbus")
            .args([
                "call",
                "--session",
                "--dest",
                "org.gnome.SessionManager",
                "--object-path",
                "/org/gnome/SessionManager/Presence",
                "--method",
                "org.gnome.SessionManager.Presence.SetStatus",
                value,
            ])
            .output();
        return output.map(|o| o.status.success()).unwrap_or(false);
    }
    #[cfg(not(any(target_os = "macos", target_os = "windows", target_os = "linux")))]
    {
        false
    }
}
