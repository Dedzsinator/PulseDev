using Microsoft.Extensions.Logging;
using PulseDev.Mobile.Services;
using PulseDev.Mobile.ViewModels;
using PulseDev.Mobile.Views;

namespace PulseDev.Mobile;

public static class MauiProgram
{
    public static MauiApp CreateMauiApp()
    {
        var builder = MauiApp.CreateBuilder();
        builder
            .UseMauiApp<App>()
            .ConfigureFonts(fonts =>
            {
                fonts.AddFont("OpenSans-Regular.ttf", "OpenSansRegular");
            });

        builder.Services.AddMauiBlazorWebView();

#if DEBUG
        builder.Services.AddLogging(configure => configure.AddDebug());
#endif

        // Register HTTP client
        builder.Services.AddHttpClient("PulseDevAPI", client =>
        {
            client.BaseAddress = new Uri("http://localhost:8000/api/v1/");
            client.DefaultRequestHeaders.Add("User-Agent", "PulseDev-Mobile/1.0");
        });

        // Register services
        builder.Services.AddSingleton<IPulseDevApiService, PulseDevApiService>();
        builder.Services.AddSingleton<ITeamService, TeamService>();
        builder.Services.AddSingleton<IAnalyticsService, AnalyticsService>();

        // Register ViewModels
        builder.Services.AddTransient<MainViewModel>();
        builder.Services.AddTransient<DashboardViewModel>();
        builder.Services.AddTransient<TeamsViewModel>();
        builder.Services.AddTransient<TeamActivityViewModel>();
        builder.Services.AddTransient<AnalyticsViewModel>();

        // Register Views
        builder.Services.AddTransient<MainPage>();
        builder.Services.AddTransient<DashboardPage>();
        builder.Services.AddTransient<TeamsPage>();
        builder.Services.AddTransient<TeamActivityPage>();
        builder.Services.AddTransient<AnalyticsPage>();

        return builder.Build();
    }
}
