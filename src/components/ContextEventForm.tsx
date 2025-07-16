import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { contextAPI } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface ContextEventFormProps {
  sessionId: string;
}

export default function ContextEventForm({ sessionId }: ContextEventFormProps) {
  const [agent, setAgent] = useState('');
  const [type, setType] = useState('');
  const [payload, setPayload] = useState('{}');
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const createEventMutation = useMutation({
    mutationFn: contextAPI.createEvent,
    onSuccess: () => {
      toast({ title: 'Event Created', description: 'Context event saved successfully' });
      queryClient.invalidateQueries({ queryKey: ['events'] });
      setPayload('{}');
    },
    onError: () => {
      toast({ title: 'Error', description: 'Failed to create event', variant: 'destructive' });
    },
  });

  const handleSubmit = () => {
    if (!agent || !type || !payload) {
      toast({ title: 'Error', description: 'All fields required', variant: 'destructive' });
      return;
    }

    try {
      const parsedPayload = JSON.parse(payload);
      createEventMutation.mutate({
        session_id: sessionId,
        agent,
        type,
        payload: parsedPayload,
      });
    } catch (error) {
      toast({ title: 'Error', description: 'Invalid JSON payload', variant: 'destructive' });
    }
  };

  const predefinedEvents = {
    'file_edit': {
      file_path: '/src/example.ts',
      change_type: 'edit',
      lines_added: 5,
      lines_removed: 2,
    },
    'terminal_command': {
      command: 'npm test',
      exit_code: 0,
      duration_ms: 2500,
    },
    'git_commit': {
      hash: 'abc123',
      message: 'feat: add new feature',
      files_changed: ['src/app.ts', 'src/utils.ts'],
    },
    'test_run': {
      framework: 'jest',
      total_tests: 42,
      passed: 40,
      failed: 2,
      duration_ms: 5000,
    },
  };

  const loadPredefinedEvent = (eventType: string) => {
    setType(eventType);
    setPayload(JSON.stringify(predefinedEvents[eventType as keyof typeof predefinedEvents], null, 2));
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create Context Event</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Select value={agent} onValueChange={setAgent}>
          <SelectTrigger>
            <SelectValue placeholder="Select agent" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="vscode">VSCode</SelectItem>
            <SelectItem value="terminal">Terminal</SelectItem>
            <SelectItem value="git">Git</SelectItem>
            <SelectItem value="browser">Browser</SelectItem>
            <SelectItem value="system">System</SelectItem>
          </SelectContent>
        </Select>

        <div className="space-y-2">
          <Input
            placeholder="Event type (e.g., file_edit, terminal_command)"
            value={type}
            onChange={(e) => setType(e.target.value)}
          />
          <div className="flex gap-2 flex-wrap">
            {Object.keys(predefinedEvents).map((eventType) => (
              <Button
                key={eventType}
                variant="outline"
                size="sm"
                onClick={() => loadPredefinedEvent(eventType)}
              >
                {eventType}
              </Button>
            ))}
          </div>
        </div>

        <Textarea
          placeholder="Event payload (JSON)"
          value={payload}
          onChange={(e) => setPayload(e.target.value)}
          rows={8}
          className="font-mono text-sm"
        />

        <Button 
          onClick={handleSubmit}
          disabled={createEventMutation.isPending}
          className="w-full"
        >
          {createEventMutation.isPending ? 'Creating...' : 'Create Event'}
        </Button>
      </CardContent>
    </Card>
  );
}