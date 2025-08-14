using System.Text.Json;
using PulseDev.Mobile.Models;

namespace PulseDev.Mobile.Services;

public interface IPulseDevApiService
{
    Task<List<TeamRoom>> GetUserTeamsAsync(string userId);
    Task<TeamRoom?> GetTeamRoomAsync(string teamId);
    Task<List<TeamActivity>> GetTeamActivityAsync(string teamId, int hours = 24);
    Task<TeamAnalytics?> GetTeamAnalyticsAsync(string teamId, string period = "week");
    Task<bool> JoinTeamAsync(string inviteCode, string username, string? email = null);
}

public class PulseDevApiService : IPulseDevApiService
{
    private readonly HttpClient _httpClient;
    private readonly JsonSerializerOptions _jsonOptions;

    public PulseDevApiService(IHttpClientFactory httpClientFactory)
    {
        _httpClient = httpClientFactory.CreateClient("PulseDevAPI");
        _jsonOptions = new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true,
            PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower
        };
    }

    public async Task<List<TeamRoom>> GetUserTeamsAsync(string userId)
    {
        try
        {
            // In real implementation, this would be a proper user teams endpoint
            // For now, mock with a single team room call
            var response = await _httpClient.GetAsync($"teams/rooms/mock-team-{userId}");

            if (response.IsSuccessStatusCode)
            {
                var json = await response.Content.ReadAsStringAsync();
                var teamRoom = JsonSerializer.Deserialize<TeamRoom>(json, _jsonOptions);
                return teamRoom != null ? new List<TeamRoom> { teamRoom } : new List<TeamRoom>();
            }

            return new List<TeamRoom>();
        }
        catch (Exception ex)
        {
            // Log error
            Console.WriteLine($"Error fetching user teams: {ex.Message}");
            return new List<TeamRoom>();
        }
    }

    public async Task<TeamRoom?> GetTeamRoomAsync(string teamId)
    {
        try
        {
            var response = await _httpClient.GetAsync($"teams/rooms/{teamId}");

            if (response.IsSuccessStatusCode)
            {
                var json = await response.Content.ReadAsStringAsync();
                return JsonSerializer.Deserialize<TeamRoom>(json, _jsonOptions);
            }

            return null;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error fetching team room: {ex.Message}");
            return null;
        }
    }

    public async Task<List<TeamActivity>> GetTeamActivityAsync(string teamId, int hours = 24)
    {
        try
        {
            var response = await _httpClient.GetAsync($"teams/rooms/{teamId}/activity?hours={hours}");

            if (response.IsSuccessStatusCode)
            {
                var json = await response.Content.ReadAsStringAsync();
                var activities = JsonSerializer.Deserialize<List<TeamActivity>>(json, _jsonOptions);
                return activities ?? new List<TeamActivity>();
            }

            return new List<TeamActivity>();
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error fetching team activity: {ex.Message}");
            return new List<TeamActivity>();
        }
    }

    public async Task<TeamAnalytics?> GetTeamAnalyticsAsync(string teamId, string period = "week")
    {
        try
        {
            var response = await _httpClient.GetAsync($"teams/rooms/{teamId}/analytics?period={period}");

            if (response.IsSuccessStatusCode)
            {
                var json = await response.Content.ReadAsStringAsync();
                return JsonSerializer.Deserialize<TeamAnalytics>(json, _jsonOptions);
            }

            return null;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error fetching team analytics: {ex.Message}");
            return null;
        }
    }

    public async Task<bool> JoinTeamAsync(string inviteCode, string username, string? email = null)
    {
        try
        {
            var requestData = new
            {
                invite_code = inviteCode,
                username = username,
                email = email
            };

            var json = JsonSerializer.Serialize(requestData, _jsonOptions);
            var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json");

            var response = await _httpClient.PostAsync("teams/join", content);

            return response.IsSuccessStatusCode;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error joining team: {ex.Message}");
            return false;
        }
    }
}

public interface ITeamService
{
    Task<List<TeamRoom>> GetMyTeamsAsync();
    Task<TeamRoom?> GetTeamDetailsAsync(string teamId);
    Task<bool> JoinTeamWithCodeAsync(string inviteCode, string username);
    string? CurrentUserId { get; set; }
}

public class TeamService : ITeamService
{
    private readonly IPulseDevApiService _apiService;

    public string? CurrentUserId { get; set; }

    public TeamService(IPulseDevApiService apiService)
    {
        _apiService = apiService;
        // In real app, get from secure storage or auth service
        CurrentUserId = Preferences.Get("current_user_id", null);
    }

    public async Task<List<TeamRoom>> GetMyTeamsAsync()
    {
        if (string.IsNullOrEmpty(CurrentUserId))
            return new List<TeamRoom>();

        return await _apiService.GetUserTeamsAsync(CurrentUserId);
    }

    public async Task<TeamRoom?> GetTeamDetailsAsync(string teamId)
    {
        return await _apiService.GetTeamRoomAsync(teamId);
    }

    public async Task<bool> JoinTeamWithCodeAsync(string inviteCode, string username)
    {
        var result = await _apiService.JoinTeamAsync(inviteCode, username);

        if (result && string.IsNullOrEmpty(CurrentUserId))
        {
            // Generate user ID if first time joining
            CurrentUserId = Guid.NewGuid().ToString();
            Preferences.Set("current_user_id", CurrentUserId);
            Preferences.Set("username", username);
        }

        return result;
    }
}

public interface IAnalyticsService
{
    Task<TeamAnalytics?> GetTeamAnalyticsAsync(string teamId, string period);
    Task<List<TeamActivity>> GetTeamActivityAsync(string teamId, int hours);
}

public class AnalyticsService : IAnalyticsService
{
    private readonly IPulseDevApiService _apiService;

    public AnalyticsService(IPulseDevApiService apiService)
    {
        _apiService = apiService;
    }

    public async Task<TeamAnalytics?> GetTeamAnalyticsAsync(string teamId, string period)
    {
        return await _apiService.GetTeamAnalyticsAsync(teamId, period);
    }

    public async Task<List<TeamActivity>> GetTeamActivityAsync(string teamId, int hours)
    {
        return await _apiService.GetTeamActivityAsync(teamId, hours);
    }
}
