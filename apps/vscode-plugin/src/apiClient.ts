import axios, { AxiosInstance } from 'axios';

export interface ContextEvent {
    sessionId: string;
    agent: string;
    type: string;
    payload: any;
    timestamp: string;
}

export class ApiClient {
    private client: AxiosInstance;

    constructor(baseURL: string) {
        this.client = axios.create({
            baseURL,
            timeout: 5000,
            headers: {
                'Content-Type': 'application/json'
            }
        });

        // Add request interceptor for error handling
        this.client.interceptors.response.use(
            response => response,
            error => {
                console.error('API request failed:', error.message);
                throw error;
            }
        );
    }

    async sendContextEvent(event: ContextEvent): Promise<void> {
        try {
            await this.client.post('/context/events', event);
        } catch (error) {
            console.error('Failed to send context event:', error);
            throw error;
        }
    }

    async getRecentContext(hours: number = 1): Promise<ContextEvent[]> {
        try {
            const response = await this.client.get(`/context/recent?hours=${hours}`);
            return response.data;
        } catch (error) {
            console.error('Failed to get recent context:', error);
            return [];
        }
    }

    async wipeContext(): Promise<void> {
        try {
            await this.client.delete('/context/wipe');
        } catch (error) {
            console.error('Failed to wipe context:', error);
            throw error;
        }
    }

    async healthCheck(): Promise<boolean> {
        try {
            await this.client.get('/health');
            return true;
        } catch (error) {
            return false;
        }
    }
}