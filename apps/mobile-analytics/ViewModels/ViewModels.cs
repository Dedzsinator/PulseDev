using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using System.Collections.ObjectModel;
using PulseDev.Mobile.Models;
using PulseDev.Mobile.Services;

namespace PulseDev.Mobile.ViewModels;

public partial class DashboardViewModel : ObservableObject
{
    private readonly IAnalyticsService _analyticsService;
    private readonly ITeamService _teamService;

    [ObservableProperty]
    private bool isLoading = true;

    [ObservableProperty]
    private string selectedPeriod = "week";

    [ObservableProperty]
    private TeamAnalytics? currentAnalytics;

    [ObservableProperty]
    private ObservableCollection<TeamRoom> userTeams = new();

    [ObservableProperty]
    private TeamRoom? selectedTeam;

    [ObservableProperty]
    private ObservableCollection<TeamActivity> recentActivities = new();

    [ObservableProperty]
    private string welcomeMessage = "Welcome to PulseDev+";

    public DashboardViewModel(IAnalyticsService analyticsService, ITeamService teamService)
    {
        _analyticsService = analyticsService;
        _teamService = teamService;
    }

    [RelayCommand]
    public async Task InitializeAsync()
    {
        IsLoading = true;

        try
        {
            // Load user teams
            var teams = await _teamService.GetMyTeamsAsync();
            UserTeams.Clear();
            foreach (var team in teams)
            {
                UserTeams.Add(team);
            }

            // Select first team by default
            if (UserTeams.Any())
            {
                SelectedTeam = UserTeams.First();
                await LoadTeamDashboardAsync();
                WelcomeMessage = $"Welcome to {SelectedTeam.Name}";
            }
            else
            {
                WelcomeMessage = "Join a team to get started!";
            }
        }
        catch (Exception ex)
        {
            // Handle error
            Console.WriteLine($"Error initializing dashboard: {ex.Message}");
        }
        finally
        {
            IsLoading = false;
        }
    }

    [RelayCommand]
    public async Task SelectTeamAsync(TeamRoom team)
    {
        SelectedTeam = team;
        await LoadTeamDashboardAsync();
    }

    [RelayCommand]
    public async Task ChangePeriodAsync(string period)
    {
        SelectedPeriod = period;
        if (SelectedTeam != null)
        {
            CurrentAnalytics = await _analyticsService.GetTeamAnalyticsAsync(SelectedTeam.Id, period);
        }
    }

    private async Task LoadTeamDashboardAsync()
    {
        if (SelectedTeam == null) return;

        IsLoading = true;

        try
        {
            // Load analytics for selected team
            CurrentAnalytics = await _analyticsService.GetTeamAnalyticsAsync(SelectedTeam.Id, SelectedPeriod);

            // Load recent activities
            var activities = await _analyticsService.GetTeamActivityAsync(SelectedTeam.Id, 24);
            RecentActivities.Clear();
            foreach (var activity in activities.Take(10))
            {
                RecentActivities.Add(activity);
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error loading team dashboard: {ex.Message}");
        }
        finally
        {
            IsLoading = false;
        }
    }

    [RelayCommand]
    public async Task RefreshAsync()
    {
        await LoadTeamDashboardAsync();
    }
}

public partial class TeamsViewModel : ObservableObject
{
    private readonly ITeamService _teamService;

    [ObservableProperty]
    private bool isLoading = true;

    [ObservableProperty]
    private ObservableCollection<TeamRoom> teams = new();

    [ObservableProperty]
    private string joinCode = string.Empty;

    [ObservableProperty]
    private string username = string.Empty;

    [ObservableProperty]
    private bool isJoining = false;

    public TeamsViewModel(ITeamService teamService)
    {
        _teamService = teamService;
        Username = Preferences.Get("username", "");
    }

    [RelayCommand]
    public async Task LoadTeamsAsync()
    {
        IsLoading = true;

        try
        {
            var userTeams = await _teamService.GetMyTeamsAsync();
            Teams.Clear();
            foreach (var team in userTeams)
            {
                Teams.Add(team);
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error loading teams: {ex.Message}");
        }
        finally
        {
            IsLoading = false;
        }
    }

    [RelayCommand]
    public async Task JoinTeamAsync()
    {
        if (string.IsNullOrWhiteSpace(JoinCode) || string.IsNullOrWhiteSpace(Username))
        {
            await Application.Current!.MainPage!.DisplayAlert("Error", "Please enter both invite code and username", "OK");
            return;
        }

        IsJoining = true;

        try
        {
            var success = await _teamService.JoinTeamWithCodeAsync(JoinCode.Trim().ToUpper(), Username.Trim());

            if (success)
            {
                await Application.Current!.MainPage!.DisplayAlert("Success", "Successfully joined team!", "OK");
                JoinCode = string.Empty;
                await LoadTeamsAsync();
            }
            else
            {
                await Application.Current!.MainPage!.DisplayAlert("Error", "Invalid invite code or team is full", "OK");
            }
        }
        catch (Exception ex)
        {
            await Application.Current!.MainPage!.DisplayAlert("Error", $"Failed to join team: {ex.Message}", "OK");
        }
        finally
        {
            IsJoining = false;
        }
    }
}

public partial class TeamActivityViewModel : ObservableObject
{
    private readonly IAnalyticsService _analyticsService;

    [ObservableProperty]
    private bool isLoading = true;

    [ObservableProperty]
    private ObservableCollection<TeamActivity> activities = new();

    [ObservableProperty]
    private string teamId = string.Empty;

    [ObservableProperty]
    private string teamName = "Team Activity";

    [ObservableProperty]
    private int selectedHours = 24;

    public List<int> HourOptions { get; } = new() { 1, 6, 24, 72, 168 }; // 1h, 6h, 1d, 3d, 1w

    public TeamActivityViewModel(IAnalyticsService analyticsService)
    {
        _analyticsService = analyticsService;
    }

    [RelayCommand]
    public async Task LoadActivityAsync()
    {
        if (string.IsNullOrEmpty(TeamId)) return;

        IsLoading = true;

        try
        {
            var teamActivities = await _analyticsService.GetTeamActivityAsync(TeamId, SelectedHours);
            Activities.Clear();
            foreach (var activity in teamActivities)
            {
                Activities.Add(activity);
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error loading team activity: {ex.Message}");
        }
        finally
        {
            IsLoading = false;
        }
    }

    [RelayCommand]
    public async Task ChangeTimeRangeAsync(int hours)
    {
        SelectedHours = hours;
        await LoadActivityAsync();
    }

    public void SetTeam(string teamId, string teamName)
    {
        TeamId = teamId;
        TeamName = $"{teamName} - Activity";
    }
}

public partial class AnalyticsViewModel : ObservableObject
{
    private readonly IAnalyticsService _analyticsService;

    [ObservableProperty]
    private bool isLoading = true;

    [ObservableProperty]
    private TeamAnalytics? analytics;

    [ObservableProperty]
    private string teamId = string.Empty;

    [ObservableProperty]
    private string teamName = "Analytics";

    [ObservableProperty]
    private string selectedPeriod = "week";

    public List<string> PeriodOptions { get; } = new() { "today", "week", "month" };

    public AnalyticsViewModel(IAnalyticsService analyticsService)
    {
        _analyticsService = analyticsService;
    }

    [RelayCommand]
    public async Task LoadAnalyticsAsync()
    {
        if (string.IsNullOrEmpty(TeamId)) return;

        IsLoading = true;

        try
        {
            Analytics = await _analyticsService.GetTeamAnalyticsAsync(TeamId, SelectedPeriod);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error loading analytics: {ex.Message}");
        }
        finally
        {
            IsLoading = false;
        }
    }

    [RelayCommand]
    public async Task ChangePeriodAsync(string period)
    {
        SelectedPeriod = period;
        await LoadAnalyticsAsync();
    }

    public void SetTeam(string teamId, string teamName)
    {
        TeamId = teamId;
        TeamName = $"{teamName} - Analytics";
    }
}
