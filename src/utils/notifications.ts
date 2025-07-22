import { invoke } from '@tauri-apps/api/tauri';

export async function notify(title: string, body: string) {
  try {
    await invoke('send_notification', { title, body });
  } catch (e) {
    // Fallback: use in-app notification system if available
    if (window?.toaster) {
      window.toaster({ title, description: body });
    } else {
      // eslint-disable-next-line no-alert
      alert(`${title}\n${body}`);
    }
  }
} 