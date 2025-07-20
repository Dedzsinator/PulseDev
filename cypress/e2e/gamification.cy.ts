describe('Gamification System', () => {
  beforeEach(() => {
    cy.interceptGamificationAPI()
    cy.visit('/dashboard')
    cy.contains('Gamification').click()
    cy.wait('@getDashboard')
  })

  it('displays user profile stats correctly', () => {
    cy.get('[data-testid="user-stats"]').within(() => {
      cy.contains('Level 8')
      cy.contains('2,500 XP')
      cy.contains('12 days') // current streak
      cy.contains('25') // longest streak
      cy.contains('156') // total commits
    })
  })

  it('shows achievement progression', () => {
    cy.get('[data-testid="achievements-section"]').within(() => {
      cy.contains('Achievements')
      
      // Should show unlocked achievements
      cy.get('[data-testid="achievement-card"]').should('have.length', 3)
      
      // Check specific achievements
      cy.contains('First Commit')
      cy.contains('Flow Master')
      cy.contains('Commit Streak')
    })
  })

  it('displays leaderboards with rankings', () => {
    cy.get('[data-testid="leaderboards"]').within(() => {
      cy.contains('XP Leaderboard')
      cy.contains('Streak Leaderboard')
      
      // Check user positioning in XP leaderboard
      cy.get('[data-testid="xp-leaderboard"]').within(() => {
        cy.contains('cypressuser')
        cy.contains('2,500')
        cy.contains('#3') // user ranking
      })
      
      // Check user positioning in streak leaderboard
      cy.get('[data-testid="streak-leaderboard"]').within(() => {
        cy.contains('cypressuser')
        cy.contains('12')
        cy.contains('#3') // user ranking
      })
    })
  })

  it('shows XP progress to next level', () => {
    cy.get('[data-testid="xp-progress"]').within(() => {
      cy.contains('Progress to Level 9')
      
      // Should show progress bar
      cy.get('[role="progressbar"]').should('exist')
    })
  })

  it('displays achievement unlock dates', () => {
    cy.get('[data-testid="achievement-card"]').first().within(() => {
      cy.contains('Unlocked:')
      cy.contains('January') // Check month is displayed
    })
  })

  it('handles empty achievements state', () => {
    cy.intercept('GET', '/api/v1/gamification/dashboard/*', {
      body: {
        success: true,
        dashboard: {
          user_stats: {
            id: 'new-user',
            username: 'newbie',
            total_xp: 0,
            level: 1,
            current_streak: 0,
            longest_streak: 0,
            total_commits: 0,
            total_flow_time: 0
          },
          achievements: [],
          leaderboards: { xp: [], streaks: [] }
        }
      }
    }).as('getEmptyDashboard')
    
    cy.reload()
    cy.contains('Gamification').click()
    cy.wait('@getEmptyDashboard')
    
    cy.contains('No achievements unlocked yet')
    cy.contains('Level 1')
    cy.contains('0 XP')
  })

  it('shows recent activity feed', () => {
    cy.get('[data-testid="activity-feed"]').should('exist')
    cy.contains('Recent Activity')
  })

  it('allows filtering leaderboard periods', () => {
    cy.get('[data-testid="leaderboard-filters"]').within(() => {
      cy.contains('Weekly').should('have.class', 'active')
      
      cy.contains('Monthly').click()
      cy.wait('@getLeaderboard')
    })
  })
})