import { invoke } from '@tauri-apps/api/tauri';

export async function pickFile(): Promise<string | null> {
  return await invoke('pick_file');
}

export async function readFile(path: string): Promise<string> {
  return await invoke('read_file', { path });
}

export async function writeFile(path: string, contents: string): Promise<void> {
  return await invoke('write_file', { path, contents });
}

export async function getDndStatus(): Promise<boolean> {
  return await invoke('get_dnd_status');
}

export async function setDndStatus(enabled: boolean): Promise<boolean> {
  return await invoke('set_dnd_status', { enabled });
} 