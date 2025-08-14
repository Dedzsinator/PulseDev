using System.Text.Json.Serialization;

namespace PulseDev.Mobile.Models;

public class TeamRoom
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("description")]
    public string? Description { get; set; }

    [JsonPropertyName("scrum_master_id")]
    public string ScrumMasterId { get; set; } = string.Empty;

    [JsonPropertyName("created_at")]
    public DateTime CreatedAt { get; set; }

    [JsonPropertyName("integrations")]
    public TeamIntegrations Integrations { get; set; } = new();

    [JsonPropertyName("members")]
    public List<TeamMember> Members { get; set; } = new();

    [JsonPropertyName("member_count")]
    public int MemberCount { get; set; }

    [JsonPropertyName("invite_codes")]
    public List<InviteCode> InviteCodes { get; set; } = new();
}

public class TeamIntegrations
{
    [JsonPropertyName("slack_channel")]
    public string? SlackChannel { get; set; }

    [JsonPropertyName("jira_project_key")]
    public string? JiraProjectKey { get; set; }
}

public class TeamMember
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("user_id")]
    public string UserId { get; set; } = string.Empty;

    [JsonPropertyName("username")]
    public string Username { get; set; } = string.Empty;

    [JsonPropertyName("email")]
    public string? Email { get; set; }

    [JsonPropertyName("role")]
    public string Role { get; set; } = string.Empty;

    [JsonPropertyName("status")]
    public string Status { get; set; } = string.Empty;

    [JsonPropertyName("joined_at")]
    public DateTime JoinedAt { get; set; }

    [JsonPropertyName("last_active")]
    public DateTime? LastActive { get; set; }

    [JsonPropertyName("total_commits")]
    public int TotalCommits { get; set; }

    [JsonPropertyName("total_xp")]
    public int TotalXp { get; set; }

    [JsonPropertyName("current_streak")]
    public int CurrentStreak { get; set; }

    [JsonPropertyName("recent_activity_count")]
    public int RecentActivityCount { get; set; }

    public string RoleDisplayName => Role.Replace("_", " ").Trim();
    public bool IsOnline => LastActive.HasValue && LastActive.Value > DateTime.UtcNow.AddMinutes(-30);
    public string StatusColor => Status switch
    {
        "active" => "#22C55E",
        "inactive" => "#F59E0B",
        _ => "#6B7280"
    };
}

public class InviteCode
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("code")]
    public string Code { get; set; } = string.Empty;

    [JsonPropertyName("role")]
    public string Role { get; set; } = string.Empty;

    [JsonPropertyName("created_at")]
    public DateTime CreatedAt { get; set; }

    [JsonPropertyName("expires_at")]
    public DateTime? ExpiresAt { get; set; }

    [JsonPropertyName("uses_remaining")]
    public int? UsesRemaining { get; set; }

    public bool IsExpired => ExpiresAt.HasValue && ExpiresAt.Value < DateTime.UtcNow;
    public string RoleDisplayName => Role.Replace("_", " ").Trim();
}

public class TeamActivity
{
    [JsonPropertyName("member_username")]
    public string MemberUsername { get; set; } = string.Empty;

    [JsonPropertyName("member_role")]
    public string MemberRole { get; set; } = string.Empty;

    [JsonPropertyName("activity_type")]
    public string ActivityType { get; set; } = string.Empty;

    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    [JsonPropertyName("details")]
    public Dictionary<string, object> Details { get; set; } = new();

    [JsonPropertyName("timestamp")]
    public DateTime Timestamp { get; set; }

    public string ActivityIcon => ActivityType switch
    {
        "file_modified" => "📝",
        "commit_created" => "🔧",
        "flow_start" => "⚡",
        "flow_end" => "🏁",
        "test_run" => "🧪",
        _ => "📊"
    };

    public string TimeAgo
    {
        get
        {
            var timespan = DateTime.UtcNow - Timestamp;
            return timespan.TotalMinutes switch
            {
                < 1 => "just now",
                < 60 => $"{(int)timespan.TotalMinutes}m ago",
                < 1440 => $"{(int)timespan.TotalHours}h ago",
                _ => $"{(int)timespan.TotalDays}d ago"
            };
        }
    }
}

public class TeamAnalytics
{
    [JsonPropertyName("team_id")]
    public string TeamId { get; set; } = string.Empty;

    [JsonPropertyName("period")]
    public string Period { get; set; } = string.Empty;

    [JsonPropertyName("active_members")]
    public int ActiveMembers { get; set; }

    [JsonPropertyName("total_commits")]
    public int TotalCommits { get; set; }

    [JsonPropertyName("total_files_changed")]
    public int TotalFilesChanged { get; set; }

    [JsonPropertyName("total_flow_sessions")]
    public int TotalFlowSessions { get; set; }

    [JsonPropertyName("total_events")]
    public int TotalEvents { get; set; }

    [JsonPropertyName("sprint_completion_rate")]
    public double SprintCompletionRate { get; set; }

    [JsonPropertyName("avg_velocity")]
    public double AvgVelocity { get; set; }

    [JsonPropertyName("top_performers")]
    public TopPerformers TopPerformers { get; set; } = new();

    [JsonPropertyName("current_sprint")]
    public CurrentSprint CurrentSprint { get; set; } = new();

    [JsonPropertyName("generated_at")]
    public DateTime GeneratedAt { get; set; }
}

public class TopPerformers
{
    [JsonPropertyName("top_committer")]
    public string? TopCommitter { get; set; }

    [JsonPropertyName("top_xp_earner")]
    public string? TopXpEarner { get; set; }

    [JsonPropertyName("longest_streak")]
    public string? LongestStreak { get; set; }
}

public class CurrentSprint
{
    [JsonPropertyName("name")]
    public string? Name { get; set; }

    [JsonPropertyName("status")]
    public string? Status { get; set; }

    [JsonPropertyName("completion_rate")]
    public double CompletionRate { get; set; }
}
