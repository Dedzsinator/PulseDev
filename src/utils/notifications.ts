// Mock Tauri import for web environment
const invoke = async (command: string, args: any) => {
  console.log(`Tauri command: ${command}`, args);
  throw new Error('Tauri not available in web environment');
};

declare global {
  interface Window {
    toaster?: (options: { title: string; description: string }) => void;
  }
}

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