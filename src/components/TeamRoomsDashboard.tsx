import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import {
    Users,
    Plus,
    Copy,
    Crown,
    Code,
    Shield,
    Eye,
    Settings,
    UserPlus,
    Link,
    Slack,
    ExternalLink,
    Clock,
    TrendingUp,
    Activity
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface TeamRoom {
    id: string;
    name: string;
    description: string;
    created_by: string;
    created_at: string;
    is_active: boolean;
    settings: {
        is_public: boolean;
        allow_guests: boolean;
        max_members: number;
    };
    integrations: {
        slack_webhook_url?: string;
        slack_channel?: string;
        jira_project_key?: string;
        jira_board_id?: string;
    };
}

interface TeamMember {
    id: string;
    team_room_id: string;
    user_id: string;
    username: string;
    role: 'scrum_master' | 'developer' | 'product_owner' | 'stakeholder' | 'guest';
    joined_at: string;
    is_active: boolean;
}

interface InviteCode {
    id: string;
    team_room_id: string;
    code: string;
    role: string;
    expires_at: string;
    max_uses: number;
    current_uses: number;
    is_active: boolean;
    created_by: string;
}

interface TeamActivity {
    id: string;
    team_room_id: string;
    user_id: string;
    username: string;
    activity_type: string;
    description: string;
    metadata: Record<string, any>;
    created_at: string;
}

interface TeamAnalytics {
    team_id: string;
    member_count: number;
    active_members_today: number;
    total_activities: number;
    activities_today: number;
    avg_session_duration: number;
    top_contributors: Array<{
        username: string;
        activity_count: number;
    }>;
    activity_trends: Array<{
        date: string;
        count: number;
    }>;
}

const API_BASE = 'http://localhost:8000/api/v1';

const teamAPI = {
    // Team Rooms
    createTeamRoom: (data: any) => fetch(`${API_BASE}/teams/rooms`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    }).then(res => res.json()),

    getTeamRooms: (userId: string) => fetch(`${API_BASE}/teams/rooms?user_id=${userId}`)
        .then(res => res.json()),

    getTeamRoom: (teamId: string) => fetch(`${API_BASE}/teams/rooms/${teamId}`)
        .then(res => res.json()),

    updateTeamRoom: (teamId: string, data: any) => fetch(`${API_BASE}/teams/rooms/${teamId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    }).then(res => res.json()),

    // Invite Codes
    generateInviteCode: (teamId: string, data: any) => fetch(`${API_BASE}/teams/rooms/${teamId}/invites`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    }).then(res => res.json()),

    getInviteCodes: (teamId: string) => fetch(`${API_BASE}/teams/rooms/${teamId}/invites`)
        .then(res => res.json()),

    joinWithCode: (data: any) => fetch(`${API_BASE}/teams/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    }).then(res => res.json()),

    // Members
    getMembers: (teamId: string) => fetch(`${API_BASE}/teams/rooms/${teamId}/members`)
        .then(res => res.json()),

    updateMemberRole: (teamId: string, memberId: string, role: string) =>
        fetch(`${API_BASE}/teams/rooms/${teamId}/members/${memberId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ role })
        }).then(res => res.json()),

    removeMember: (teamId: string, memberId: string) =>
        fetch(`${API_BASE}/teams/rooms/${teamId}/members/${memberId}`, {
            method: 'DELETE'
        }).then(res => res.json()),

    // Integrations
    updateIntegrations: (teamId: string, data: any) =>
        fetch(`${API_BASE}/teams/rooms/${teamId}/integrations`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }).then(res => res.json()),

    // Activity & Analytics
    getActivity: (teamId: string, limit?: number) =>
        fetch(`${API_BASE}/teams/rooms/${teamId}/activity${limit ? `?limit=${limit}` : ''}`)
            .then(res => res.json()),

    getAnalytics: (teamId: string, period?: string) =>
        fetch(`${API_BASE}/teams/rooms/${teamId}/analytics${period ? `?period=${period}` : ''}`)
            .then(res => res.json()),
};

const getRoleIcon = (role: string) => {
    switch (role) {
        case 'scrum_master': return Crown;
        case 'developer': return Code;
        case 'product_owner': return Shield;
        case 'stakeholder': return Eye;
        case 'guest': return UserPlus;
        default: return Users;
    }
};

const getRoleColor = (role: string) => {
    switch (role) {
        case 'scrum_master': return 'default';
        case 'developer': return 'secondary';
        case 'product_owner': return 'outline';
        case 'stakeholder': return 'outline';
        case 'guest': return 'outline';
        default: return 'outline';
    }
};

const getCurrentUserId = () => {
    return localStorage.getItem('user_id') || 'user_' + Date.now();
};

export default function TeamRoomsDashboard() {
    const [currentUserId] = useState(getCurrentUserId());
    const [selectedTeam, setSelectedTeam] = useState<string | null>(null);
    const [showCreateRoom, setShowCreateRoom] = useState(false);
    const [showJoinRoom, setShowJoinRoom] = useState(false);
    const [showInviteDialog, setShowInviteDialog] = useState(false);
    const [showSettingsDialog, setShowSettingsDialog] = useState(false);
    const [joinCode, setJoinCode] = useState('');

    // Form states
    const [newRoomName, setNewRoomName] = useState('');
    const [newRoomDescription, setNewRoomDescription] = useState('');
    const [newRoomSettings, setNewRoomSettings] = useState({
        is_public: false,
        allow_guests: true,
        max_members: 20
    });

    const [inviteSettings, setInviteSettings] = useState({
        role: 'developer',
        expires_in_days: 7,
        max_uses: 10
    });

    const { toast } = useToast();
    const queryClient = useQueryClient();

    // Fetch team rooms
    const { data: teamRooms, isLoading: roomsLoading } = useQuery({
        queryKey: ['team-rooms', currentUserId],
        queryFn: () => teamAPI.getTeamRooms(currentUserId),
    });

    // Fetch selected team details
    const { data: selectedTeamData } = useQuery({
        queryKey: ['team-room', selectedTeam],
        queryFn: () => teamAPI.getTeamRoom(selectedTeam!),
        enabled: !!selectedTeam,
    });

    // Fetch team members
    const { data: teamMembers } = useQuery({
        queryKey: ['team-members', selectedTeam],
        queryFn: () => teamAPI.getMembers(selectedTeam!),
        enabled: !!selectedTeam,
    });

    // Fetch invite codes
    const { data: inviteCodes } = useQuery({
        queryKey: ['invite-codes', selectedTeam],
        queryFn: () => teamAPI.getInviteCodes(selectedTeam!),
        enabled: !!selectedTeam,
    });

    // Fetch team activity
    const { data: teamActivity } = useQuery({
        queryKey: ['team-activity', selectedTeam],
        queryFn: () => teamAPI.getActivity(selectedTeam!, 20),
        enabled: !!selectedTeam,
    });

    // Fetch team analytics
    const { data: teamAnalytics } = useQuery({
        queryKey: ['team-analytics', selectedTeam],
        queryFn: () => teamAPI.getAnalytics(selectedTeam!),
        enabled: !!selectedTeam,
    });

    // Mutations
    const createRoomMutation = useMutation({
        mutationFn: teamAPI.createTeamRoom,
        onSuccess: (data) => {
            toast({ title: 'Team room created successfully!' });
            setShowCreateRoom(false);
            setNewRoomName('');
            setNewRoomDescription('');
            queryClient.invalidateQueries({ queryKey: ['team-rooms'] });
            setSelectedTeam(data.id);
        },
        onError: () => {
            toast({ title: 'Error creating team room', variant: 'destructive' });
        }
    });

    const joinRoomMutation = useMutation({
        mutationFn: teamAPI.joinWithCode,
        onSuccess: (data) => {
            toast({ title: 'Successfully joined team room!' });
            setShowJoinRoom(false);
            setJoinCode('');
            queryClient.invalidateQueries({ queryKey: ['team-rooms'] });
            setSelectedTeam(data.team_room_id);
        },
        onError: () => {
            toast({ title: 'Error joining team room', variant: 'destructive' });
        }
    });

    const generateInviteMutation = useMutation({
        mutationFn: ({ teamId, data }: { teamId: string; data: any }) =>
            teamAPI.generateInviteCode(teamId, data),
        onSuccess: () => {
            toast({ title: 'Invite code generated!' });
            setShowInviteDialog(false);
            queryClient.invalidateQueries({ queryKey: ['invite-codes'] });
        }
    });

    const handleCreateRoom = () => {
        if (!newRoomName.trim()) {
            toast({ title: 'Please enter a room name', variant: 'destructive' });
            return;
        }

        createRoomMutation.mutate({
            name: newRoomName,
            description: newRoomDescription,
            created_by: currentUserId,
            settings: newRoomSettings
        });
    };

    const handleJoinRoom = () => {
        if (!joinCode.trim()) {
            toast({ title: 'Please enter an invite code', variant: 'destructive' });
            return;
        }

        joinRoomMutation.mutate({
            invite_code: joinCode,
            user_id: currentUserId,
            username: `User${currentUserId.slice(-4)}`
        });
    };

    const handleGenerateInvite = () => {
        if (!selectedTeam) return;

        const expiresAt = new Date();
        expiresAt.setDate(expiresAt.getDate() + inviteSettings.expires_in_days);

        generateInviteMutation.mutate({
            teamId: selectedTeam,
            data: {
                role: inviteSettings.role,
                expires_at: expiresAt.toISOString(),
                max_uses: inviteSettings.max_uses,
                created_by: currentUserId
            }
        });
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
        toast({ title: 'Copied to clipboard!' });
    };

    if (roomsLoading) {
        return <div className="flex items-center justify-center h-64">Loading team rooms...</div>;
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold">Team Collaboration</h2>
                <div className="flex gap-2">
                    <Dialog open={showJoinRoom} onOpenChange={setShowJoinRoom}>
                        <DialogTrigger asChild>
                            <Button variant="outline">
                                <Link className="w-4 h-4 mr-2" />
                                Join Team
                            </Button>
                        </DialogTrigger>
                        <DialogContent>
                            <DialogHeader>
                                <DialogTitle>Join Team Room</DialogTitle>
                            </DialogHeader>
                            <div className="space-y-4">
                                <div>
                                    <Label htmlFor="join-code">Invite Code</Label>
                                    <Input
                                        id="join-code"
                                        value={joinCode}
                                        onChange={(e) => setJoinCode(e.target.value)}
                                        placeholder="Enter invite code"
                                    />
                                </div>
                                <Button onClick={handleJoinRoom} disabled={joinRoomMutation.isPending}>
                                    {joinRoomMutation.isPending ? 'Joining...' : 'Join Team'}
                                </Button>
                            </div>
                        </DialogContent>
                    </Dialog>

                    <Dialog open={showCreateRoom} onOpenChange={setShowCreateRoom}>
                        <DialogTrigger asChild>
                            <Button>
                                <Plus className="w-4 h-4 mr-2" />
                                Create Team
                            </Button>
                        </DialogTrigger>
                        <DialogContent>
                            <DialogHeader>
                                <DialogTitle>Create New Team Room</DialogTitle>
                            </DialogHeader>
                            <div className="space-y-4">
                                <div>
                                    <Label htmlFor="room-name">Team Name</Label>
                                    <Input
                                        id="room-name"
                                        value={newRoomName}
                                        onChange={(e) => setNewRoomName(e.target.value)}
                                        placeholder="My Awesome Team"
                                    />
                                </div>
                                <div>
                                    <Label htmlFor="room-description">Description</Label>
                                    <Textarea
                                        id="room-description"
                                        value={newRoomDescription}
                                        onChange={(e) => setNewRoomDescription(e.target.value)}
                                        placeholder="Describe your team's purpose and goals"
                                    />
                                </div>
                                <div className="space-y-3">
                                    <Label>Team Settings</Label>
                                    <div className="flex items-center justify-between">
                                        <Label htmlFor="is-public">Public Team</Label>
                                        <Switch
                                            id="is-public"
                                            checked={newRoomSettings.is_public}
                                            onCheckedChange={(checked) =>
                                                setNewRoomSettings(prev => ({ ...prev, is_public: checked }))}
                                        />
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <Label htmlFor="allow-guests">Allow Guests</Label>
                                        <Switch
                                            id="allow-guests"
                                            checked={newRoomSettings.allow_guests}
                                            onCheckedChange={(checked) =>
                                                setNewRoomSettings(prev => ({ ...prev, allow_guests: checked }))}
                                        />
                                    </div>
                                    <div>
                                        <Label htmlFor="max-members">Max Members</Label>
                                        <Input
                                            id="max-members"
                                            type="number"
                                            min="1"
                                            max="100"
                                            value={newRoomSettings.max_members}
                                            onChange={(e) =>
                                                setNewRoomSettings(prev => ({ ...prev, max_members: parseInt(e.target.value) }))}
                                        />
                                    </div>
                                </div>
                                <Button onClick={handleCreateRoom} disabled={createRoomMutation.isPending}>
                                    {createRoomMutation.isPending ? 'Creating...' : 'Create Team'}
                                </Button>
                            </div>
                        </DialogContent>
                    </Dialog>
                </div>
            </div>

            <div className="grid grid-cols-12 gap-6">
                {/* Team Rooms Sidebar */}
                <div className="col-span-3">
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-lg">Your Teams</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2">
                            {teamRooms?.map((room: TeamRoom) => (
                                <div
                                    key={room.id}
                                    className={`p-3 rounded-lg cursor-pointer transition-colors ${selectedTeam === room.id
                                            ? 'bg-primary text-primary-foreground'
                                            : 'hover:bg-muted'
                                        }`}
                                    onClick={() => setSelectedTeam(room.id)}
                                >
                                    <div className="font-medium truncate">{room.name}</div>
                                    <div className="text-sm opacity-70 truncate">{room.description}</div>
                                    <div className="flex items-center gap-2 mt-2">
                                        <Badge variant="outline" className="text-xs">
                                            {room.is_active ? 'Active' : 'Inactive'}
                                        </Badge>
                                        {room.settings.is_public && (
                                            <Badge variant="outline" className="text-xs">Public</Badge>
                                        )}
                                    </div>
                                </div>
                            ))}
                            {(!teamRooms || teamRooms.length === 0) && (
                                <div className="text-center py-8 text-muted-foreground">
                                    <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
                                    <p>No team rooms yet</p>
                                    <p className="text-sm">Create or join a team to get started</p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>

                {/* Main Content */}
                <div className="col-span-9">
                    {selectedTeam ? (
                        <Tabs defaultValue="overview" className="space-y-4">
                            <TabsList>
                                <TabsTrigger value="overview">Overview</TabsTrigger>
                                <TabsTrigger value="members">Members</TabsTrigger>
                                <TabsTrigger value="invites">Invites</TabsTrigger>
                                <TabsTrigger value="activity">Activity</TabsTrigger>
                                <TabsTrigger value="analytics">Analytics</TabsTrigger>
                                <TabsTrigger value="integrations">Integrations</TabsTrigger>
                            </TabsList>

                            <TabsContent value="overview" className="space-y-4">
                                <Card>
                                    <CardHeader>
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <CardTitle>{selectedTeamData?.name}</CardTitle>
                                                <p className="text-muted-foreground mt-1">
                                                    {selectedTeamData?.description}
                                                </p>
                                            </div>
                                            <Button variant="outline" size="sm">
                                                <Settings className="w-4 h-4 mr-2" />
                                                Settings
                                            </Button>
                                        </div>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="grid grid-cols-3 gap-4">
                                            <div className="text-center">
                                                <div className="text-2xl font-bold">{teamMembers?.length || 0}</div>
                                                <div className="text-sm text-muted-foreground">Members</div>
                                            </div>
                                            <div className="text-center">
                                                <div className="text-2xl font-bold">{teamAnalytics?.activities_today || 0}</div>
                                                <div className="text-sm text-muted-foreground">Activities Today</div>
                                            </div>
                                            <div className="text-center">
                                                <div className="text-2xl font-bold">
                                                    {teamAnalytics?.active_members_today || 0}
                                                </div>
                                                <div className="text-sm text-muted-foreground">Active Today</div>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>

                                {/* Recent Activity */}
                                <Card>
                                    <CardHeader>
                                        <CardTitle>Recent Activity</CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="space-y-3">
                                            {teamActivity?.slice(0, 5).map((activity: TeamActivity) => (
                                                <div key={activity.id} className="flex items-center gap-3 p-3 rounded-lg bg-muted">
                                                    <Activity className="w-4 h-4 text-muted-foreground" />
                                                    <div className="flex-1">
                                                        <div className="font-medium">{activity.username}</div>
                                                        <div className="text-sm text-muted-foreground">{activity.description}</div>
                                                    </div>
                                                    <div className="text-xs text-muted-foreground">
                                                        {new Date(activity.created_at).toLocaleTimeString()}
                                                    </div>
                                                </div>
                                            ))}
                                            {(!teamActivity || teamActivity.length === 0) && (
                                                <div className="text-center py-8 text-muted-foreground">
                                                    No recent activity
                                                </div>
                                            )}
                                        </div>
                                    </CardContent>
                                </Card>
                            </TabsContent>

                            <TabsContent value="members" className="space-y-4">
                                <Card>
                                    <CardHeader>
                                        <div className="flex items-center justify-between">
                                            <CardTitle>Team Members</CardTitle>
                                            <Dialog open={showInviteDialog} onOpenChange={setShowInviteDialog}>
                                                <DialogTrigger asChild>
                                                    <Button>
                                                        <UserPlus className="w-4 h-4 mr-2" />
                                                        Invite Member
                                                    </Button>
                                                </DialogTrigger>
                                                <DialogContent>
                                                    <DialogHeader>
                                                        <DialogTitle>Generate Invite Code</DialogTitle>
                                                    </DialogHeader>
                                                    <div className="space-y-4">
                                                        <div>
                                                            <Label htmlFor="invite-role">Role</Label>
                                                            <Select
                                                                value={inviteSettings.role}
                                                                onValueChange={(value) =>
                                                                    setInviteSettings(prev => ({ ...prev, role: value }))}
                                                            >
                                                                <SelectTrigger>
                                                                    <SelectValue />
                                                                </SelectTrigger>
                                                                <SelectContent>
                                                                    <SelectItem value="developer">Developer</SelectItem>
                                                                    <SelectItem value="scrum_master">Scrum Master</SelectItem>
                                                                    <SelectItem value="product_owner">Product Owner</SelectItem>
                                                                    <SelectItem value="stakeholder">Stakeholder</SelectItem>
                                                                    <SelectItem value="guest">Guest</SelectItem>
                                                                </SelectContent>
                                                            </Select>
                                                        </div>
                                                        <div>
                                                            <Label htmlFor="expires-days">Expires in (days)</Label>
                                                            <Input
                                                                id="expires-days"
                                                                type="number"
                                                                min="1"
                                                                max="30"
                                                                value={inviteSettings.expires_in_days}
                                                                onChange={(e) =>
                                                                    setInviteSettings(prev => ({ ...prev, expires_in_days: parseInt(e.target.value) }))}
                                                            />
                                                        </div>
                                                        <div>
                                                            <Label htmlFor="max-uses">Max Uses</Label>
                                                            <Input
                                                                id="max-uses"
                                                                type="number"
                                                                min="1"
                                                                max="100"
                                                                value={inviteSettings.max_uses}
                                                                onChange={(e) =>
                                                                    setInviteSettings(prev => ({ ...prev, max_uses: parseInt(e.target.value) }))}
                                                            />
                                                        </div>
                                                        <Button onClick={handleGenerateInvite} disabled={generateInviteMutation.isPending}>
                                                            {generateInviteMutation.isPending ? 'Generating...' : 'Generate Invite'}
                                                        </Button>
                                                    </div>
                                                </DialogContent>
                                            </Dialog>
                                        </div>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="space-y-3">
                                            {teamMembers?.map((member: TeamMember) => {
                                                const RoleIcon = getRoleIcon(member.role);
                                                return (
                                                    <div key={member.id} className="flex items-center justify-between p-3 rounded-lg border">
                                                        <div className="flex items-center gap-3">
                                                            <RoleIcon className="w-5 h-5" />
                                                            <div>
                                                                <div className="font-medium">{member.username}</div>
                                                                <div className="text-sm text-muted-foreground">
                                                                    Joined {new Date(member.joined_at).toLocaleDateString()}
                                                                </div>
                                                            </div>
                                                        </div>
                                                        <div className="flex items-center gap-2">
                                                            <Badge variant={getRoleColor(member.role)}>
                                                                {member.role.replace('_', ' ')}
                                                            </Badge>
                                                            <Badge variant={member.is_active ? 'default' : 'outline'}>
                                                                {member.is_active ? 'Active' : 'Inactive'}
                                                            </Badge>
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </CardContent>
                                </Card>
                            </TabsContent>

                            <TabsContent value="invites" className="space-y-4">
                                <Card>
                                    <CardHeader>
                                        <CardTitle>Invite Codes</CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="space-y-3">
                                            {inviteCodes?.map((invite: InviteCode) => (
                                                <div key={invite.id} className="flex items-center justify-between p-3 rounded-lg border">
                                                    <div className="flex-1">
                                                        <div className="flex items-center gap-2">
                                                            <code className="bg-muted px-2 py-1 rounded text-sm font-mono">
                                                                {invite.code}
                                                            </code>
                                                            <Button
                                                                variant="ghost"
                                                                size="sm"
                                                                onClick={() => copyToClipboard(invite.code)}
                                                            >
                                                                <Copy className="w-4 h-4" />
                                                            </Button>
                                                        </div>
                                                        <div className="text-sm text-muted-foreground mt-1">
                                                            Role: {invite.role} • Uses: {invite.current_uses}/{invite.max_uses} •
                                                            Expires: {new Date(invite.expires_at).toLocaleDateString()}
                                                        </div>
                                                    </div>
                                                    <Badge variant={invite.is_active ? 'default' : 'outline'}>
                                                        {invite.is_active ? 'Active' : 'Expired'}
                                                    </Badge>
                                                </div>
                                            ))}
                                            {(!inviteCodes || inviteCodes.length === 0) && (
                                                <div className="text-center py-8 text-muted-foreground">
                                                    No invite codes generated yet
                                                </div>
                                            )}
                                        </div>
                                    </CardContent>
                                </Card>
                            </TabsContent>

                            <TabsContent value="activity" className="space-y-4">
                                <Card>
                                    <CardHeader>
                                        <CardTitle>Team Activity Feed</CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="space-y-3">
                                            {teamActivity?.map((activity: TeamActivity) => (
                                                <div key={activity.id} className="flex items-start gap-3 p-3 rounded-lg bg-muted">
                                                    <Activity className="w-5 h-5 mt-0.5 text-muted-foreground" />
                                                    <div className="flex-1">
                                                        <div className="flex items-center gap-2">
                                                            <span className="font-medium">{activity.username}</span>
                                                            <span className="text-sm text-muted-foreground">
                                                                {activity.activity_type}
                                                            </span>
                                                        </div>
                                                        <div className="text-sm mt-1">{activity.description}</div>
                                                        {activity.metadata && Object.keys(activity.metadata).length > 0 && (
                                                            <div className="text-xs text-muted-foreground mt-2">
                                                                {JSON.stringify(activity.metadata)}
                                                            </div>
                                                        )}
                                                        <div className="text-xs text-muted-foreground mt-2">
                                                            {new Date(activity.created_at).toLocaleString()}
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </CardContent>
                                </Card>
                            </TabsContent>

                            <TabsContent value="analytics" className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <Card>
                                        <CardHeader>
                                            <CardTitle className="flex items-center gap-2">
                                                <TrendingUp className="w-5 h-5" />
                                                Team Metrics
                                            </CardTitle>
                                        </CardHeader>
                                        <CardContent className="space-y-4">
                                            <div className="flex justify-between items-center">
                                                <span>Total Members</span>
                                                <span className="font-bold">{teamAnalytics?.member_count || 0}</span>
                                            </div>
                                            <div className="flex justify-between items-center">
                                                <span>Active Today</span>
                                                <span className="font-bold">{teamAnalytics?.active_members_today || 0}</span>
                                            </div>
                                            <div className="flex justify-between items-center">
                                                <span>Total Activities</span>
                                                <span className="font-bold">{teamAnalytics?.total_activities || 0}</span>
                                            </div>
                                            <div className="flex justify-between items-center">
                                                <span>Avg Session (min)</span>
                                                <span className="font-bold">
                                                    {Math.round((teamAnalytics?.avg_session_duration || 0) / 60)}
                                                </span>
                                            </div>
                                        </CardContent>
                                    </Card>

                                    <Card>
                                        <CardHeader>
                                            <CardTitle>Top Contributors</CardTitle>
                                        </CardHeader>
                                        <CardContent>
                                            <div className="space-y-3">
                                                {teamAnalytics?.top_contributors?.map((contributor, index) => (
                                                    <div key={index} className="flex items-center justify-between">
                                                        <div className="flex items-center gap-2">
                                                            <Badge variant="outline">{index + 1}</Badge>
                                                            <span className="font-medium">{contributor.username}</span>
                                                        </div>
                                                        <span className="text-sm text-muted-foreground">
                                                            {contributor.activity_count} activities
                                                        </span>
                                                    </div>
                                                ))}
                                            </div>
                                        </CardContent>
                                    </Card>
                                </div>
                            </TabsContent>

                            <TabsContent value="integrations" className="space-y-4">
                                <Card>
                                    <CardHeader>
                                        <CardTitle>Team Integrations</CardTitle>
                                        <p className="text-sm text-muted-foreground">
                                            Connect your team room with external tools for seamless collaboration.
                                        </p>
                                    </CardHeader>
                                    <CardContent className="space-y-6">
                                        {/* Slack Integration */}
                                        <div className="border rounded-lg p-4">
                                            <div className="flex items-center gap-3 mb-4">
                                                <Slack className="w-6 h-6" />
                                                <div>
                                                    <h3 className="font-semibold">Slack Integration</h3>
                                                    <p className="text-sm text-muted-foreground">
                                                        Get notifications and updates in your Slack channel
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="space-y-3">
                                                <div>
                                                    <Label htmlFor="slack-webhook">Slack Webhook URL</Label>
                                                    <Input
                                                        id="slack-webhook"
                                                        placeholder="https://hooks.slack.com/services/..."
                                                        value={selectedTeamData?.integrations?.slack_webhook_url || ''}
                                                    />
                                                </div>
                                                <div>
                                                    <Label htmlFor="slack-channel">Slack Channel</Label>
                                                    <Input
                                                        id="slack-channel"
                                                        placeholder="#development"
                                                        value={selectedTeamData?.integrations?.slack_channel || ''}
                                                    />
                                                </div>
                                                <Button variant="outline" size="sm">
                                                    Test Integration
                                                </Button>
                                            </div>
                                        </div>

                                        {/* Jira Integration */}
                                        <div className="border rounded-lg p-4">
                                            <div className="flex items-center gap-3 mb-4">
                                                <ExternalLink className="w-6 h-6" />
                                                <div>
                                                    <h3 className="font-semibold">Jira Integration</h3>
                                                    <p className="text-sm text-muted-foreground">
                                                        Sync tickets and track progress with Jira
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="space-y-3">
                                                <div>
                                                    <Label htmlFor="jira-project">Jira Project Key</Label>
                                                    <Input
                                                        id="jira-project"
                                                        placeholder="PROJ"
                                                        value={selectedTeamData?.integrations?.jira_project_key || ''}
                                                    />
                                                </div>
                                                <div>
                                                    <Label htmlFor="jira-board">Jira Board ID</Label>
                                                    <Input
                                                        id="jira-board"
                                                        placeholder="123"
                                                        value={selectedTeamData?.integrations?.jira_board_id || ''}
                                                    />
                                                </div>
                                                <Button variant="outline" size="sm">
                                                    Connect to Jira
                                                </Button>
                                            </div>
                                        </div>

                                        <div className="flex gap-2">
                                            <Button>Save Integrations</Button>
                                            <Button variant="outline">Test All</Button>
                                        </div>
                                    </CardContent>
                                </Card>
                            </TabsContent>
                        </Tabs>
                    ) : (
                        <Card>
                            <CardContent className="flex items-center justify-center h-64">
                                <div className="text-center">
                                    <Users className="w-16 h-16 mx-auto mb-4 opacity-50" />
                                    <h3 className="text-lg font-semibold mb-2">Select a Team Room</h3>
                                    <p className="text-muted-foreground">
                                        Choose a team from the sidebar or create a new one to get started
                                    </p>
                                </div>
                            </CardContent>
                        </Card>
                    )}
                </div>
            </div>
        </div>
    );
}
