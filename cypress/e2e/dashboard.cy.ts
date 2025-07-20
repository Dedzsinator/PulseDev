describe('CCM Dashboard', () => {
  beforeEach(() => {
    cy.interceptGamificationAPI()
    cy.visitDashboard()
  })

  it('loads and displays main dashboard', () => {
    cy.contains('PulseDev+ Cognitive Context Mirror')
    cy.contains('System Metrics')
    cy.contains('CCM Features')
    cy.contains('Context Event Form')
  })

  it('allows switching between tabs', () => {
    // Test tab navigation
    cy.get('[role="tablist"]').within(() => {
      cy.contains('System').should('have.attr', 'data-state', 'active')
      
      cy.contains('Gamification').click()
      cy.contains('Gamification').should('have.attr', 'data-state', 'active')
      
      cy.contains('Features').click()
      cy.contains('Features').should('have.attr', 'data-state', 'active')
    })
  })

  it('displays system metrics', () => {
    cy.get('[data-testid="system-metrics"]').within(() => {
      cy.contains('CPU Usage')
      cy.contains('Memory Usage')
      cy.contains('Active Sessions')
      cy.contains('Events/Hour')
    })
  })

  it('shows CCM features status', () => {
    cy.contains('Features').click()
    
    cy.get('[data-testid="ccm-features"]').within(() => {
      cy.contains('AI Context Generation')
      cy.contains('Git Auto-Commit')
      cy.contains('Flow Detection')
      cy.contains('Energy Scoring')
    })
  })

  it('allows submitting context events', () => {
    cy.contains('Events').click()
    
    cy.submitContextEvent({
      agent: 'vscode',
      type: 'file_edit',
      payload: { file: 'test.ts', changes: 'added function' }
    })
    
    cy.contains('Event submitted successfully').should('be.visible')
  })

  it('displays gamification dashboard', () => {
    cy.contains('Gamification').click()
    cy.wait('@getDashboard')
    
    cy.get('[data-testid="gamification-dashboard"]').within(() => {
      // User stats
      cy.contains('Level 8')
      cy.contains('2,500 XP')
      cy.contains('12 days') // current streak
      
      // Achievements
      cy.contains('Achievements')
      cy.contains('First Commit')
      cy.contains('Flow Master')
      
      // Leaderboards
      cy.contains('XP Leaderboard')
      cy.contains('Streak Leaderboard')
    })
  })

  it('shows achievement details on hover', () => {
    cy.contains('Gamification').click()
    cy.wait('@getDashboard')
    
    cy.get('[data-testid="achievement-card"]').first().trigger('mouseover')
    cy.contains('Made your first commit').should('be.visible')
  })

  it('handles API errors gracefully', () => {
    cy.intercept('GET', '/api/v1/gamification/dashboard/*', {
      statusCode: 500,
      body: { error: 'Internal Server Error' }
    }).as('getErrorDashboard')
    
    cy.contains('Gamification').click()
    cy.wait('@getErrorDashboard')
    
    cy.contains('Error loading gamification data').should('be.visible')
  })
})